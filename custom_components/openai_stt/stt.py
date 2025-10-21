"""Setting up OpenAISTTProvider."""

from __future__ import annotations

from collections.abc import AsyncIterable
import logging

import voluptuous as vol

from homeassistant.components.stt import (
    AudioBitRates,
    AudioChannels,
    AudioCodecs,
    AudioFormats,
    AudioSampleRates,
    Provider,
    SpeechMetadata,
    SpeechResult,
    SpeechToTextEntity,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_API_URL,
    CONF_MODEL,
    CONF_NOISE_REDUCTION,
    CONF_PROMPT,
    CONF_REALTIME,
    CONF_TEMPERATURE,
    DEFAULT_API_URL,
    DEFAULT_MODEL,
    DEFAULT_NOISE_REDUCTION,
    DEFAULT_PROMPT,
    DEFAULT_REALTIME,
    DEFAULT_TEMPERATURE,
    DOMAIN,
)
from .http_client import OpenAIHTTPClient
from .websocket_client import OpenAIWebSocketClient

_LOGGER = logging.getLogger(__name__)

# Legacy YAML support - keep these for backward compatibility
CONF_TEMP = "temperature"
DEFAULT_TEMP = DEFAULT_TEMPERATURE

SUPPORTED_MODELS = [
    "whisper-1",
    "gpt-4o-mini-transcribe",
    "gpt-4o-transcribe",
]

SUPPORTED_NOISE_REDUCTION = [
    None,
    "near_field",
    "far_field",
]

SUPPORTED_LANGUAGES = [
    "af",
    "ar",
    "hy",
    "az",
    "be",
    "bs",
    "bg",
    "ca",
    "zh",
    "hr",
    "cs",
    "da",
    "nl",
    "en",
    "et",
    "fi",
    "fr",
    "gl",
    "de",
    "el",
    "he",
    "hi",
    "hu",
    "is",
    "id",
    "it",
    "ja",
    "kn",
    "kk",
    "ko",
    "lv",
    "lt",
    "mk",
    "ms",
    "mr",
    "mi",
    "ne",
    "no",
    "fa",
    "pl",
    "pt",
    "ro",
    "ru",
    "sr",
    "sk",
    "sl",
    "es",
    "sw",
    "sv",
    "tl",
    "ta",
    "th",
    "tr",
    "uk",
    "ur",
    "vi",
    "cy",
]

MODEL_SCHEMA = vol.In(SUPPORTED_MODELS)
NOISE_REDUCTION_SCHEMA = vol.In(SUPPORTED_NOISE_REDUCTION)

PLATFORM_SCHEMA = cv.PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Optional(CONF_API_URL, default=DEFAULT_API_URL): cv.string,
        vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): MODEL_SCHEMA,
        vol.Optional(CONF_PROMPT, default=DEFAULT_PROMPT): cv.string,
        vol.Optional(CONF_TEMP, default=DEFAULT_TEMP): cv.positive_int,
        vol.Optional(CONF_REALTIME, default=DEFAULT_REALTIME): cv.boolean,
        vol.Optional(
            CONF_NOISE_REDUCTION, default=DEFAULT_NOISE_REDUCTION
        ): NOISE_REDUCTION_SCHEMA,
    }
)


async def async_get_engine(
    hass: HomeAssistant, config: dict, discovery_info: dict | None = None
) -> OpenAISTTProvider:
    """Return the OpenAI STT provider (legacy YAML support)."""
    api_key = config[CONF_API_KEY]
    api_url = config.get(CONF_API_URL, DEFAULT_API_URL)
    model = config.get(CONF_MODEL, DEFAULT_MODEL)
    prompt = config.get(CONF_PROMPT, DEFAULT_PROMPT)
    temperature = config.get(CONF_TEMP, DEFAULT_TEMP)
    realtime = config.get(CONF_REALTIME, DEFAULT_REALTIME)
    noise_reduction = config.get(CONF_NOISE_REDUCTION, DEFAULT_NOISE_REDUCTION)

    return OpenAISTTProvider(
        hass, api_key, api_url, model, prompt, temperature, realtime, noise_reduction
    )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OpenAI STT from a config entry."""
    config_data = hass.data[DOMAIN][config_entry.entry_id]

    api_key = config_data[CONF_API_KEY]
    api_url = config_data.get(CONF_API_URL, DEFAULT_API_URL)
    model = config_data.get(CONF_MODEL, DEFAULT_MODEL)
    prompt = config_data.get(CONF_PROMPT, DEFAULT_PROMPT)
    temperature = config_data.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE)
    realtime = config_data.get(CONF_REALTIME, DEFAULT_REALTIME)
    noise_reduction = config_data.get(CONF_NOISE_REDUCTION, DEFAULT_NOISE_REDUCTION)

    entity = OpenAISTTEntity(
        config_entry,
        api_key,
        api_url,
        model,
        prompt,
        temperature,
        realtime,
        noise_reduction,
    )
    async_add_entities([entity])


class OpenAISTTProvider(Provider):
    """The OpenAI STT provider."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_key: str,
        api_url: str,
        model: str,
        prompt: str,
        temperature: int,
        realtime: bool,
        noise_reduction: str,
    ) -> None:
        """Init OpenAI STT service."""
        self.hass = hass
        self.name = "OpenAI STT"

        self._api_key = api_key
        self._api_url = api_url
        self._model = model
        self._prompt = prompt
        self._temperature = temperature
        self._realtime = realtime
        self._noise_reduction = noise_reduction
        self._client = self._create_client()

    @property
    def supported_languages(self) -> list[str]:
        """Return a list of supported languages."""
        return SUPPORTED_LANGUAGES

    @property
    def supported_formats(self) -> list[AudioFormats]:
        """Return a list of supported formats."""
        return [AudioFormats.WAV, AudioFormats.OGG]

    @property
    def supported_codecs(self) -> list[AudioCodecs]:
        """Return a list of supported codecs."""
        return [AudioCodecs.PCM, AudioCodecs.OPUS]

    @property
    def supported_bit_rates(self) -> list[AudioBitRates]:
        """Return a list of supported bitrates."""
        return [AudioBitRates.BITRATE_16]

    @property
    def supported_sample_rates(self) -> list[AudioSampleRates]:
        """Return a list of supported samplerates."""
        return [AudioSampleRates.SAMPLERATE_16000]

    @property
    def supported_channels(self) -> list[AudioChannels]:
        """Return a list of supported channels."""
        return [AudioChannels.CHANNEL_MONO]

    def _create_client(self):
        """Create and return the appropriate client based on configuration."""
        if self._realtime:
            # Use WebSocket client for OpenAI Realtime API
            return OpenAIWebSocketClient(
                async_get_clientsession(self.hass),
                self._api_key,
                self._api_url,
                self._model,
                self._prompt,
                self._noise_reduction,
            )

        # Use HTTP client for OpenAI Transcription API
        return OpenAIHTTPClient(
            async_get_clientsession(self.hass),
            self._api_key,
            self._api_url,
            self._model,
            self._prompt,
            self._temperature,
        )

    async def async_process_audio_stream(
        self, metadata: SpeechMetadata, stream: AsyncIterable[bytes]
    ) -> SpeechResult:
        """Process audio stream using the configured method (HTTP or WebSocket)."""
        _LOGGER.debug(
            "Processing audio stream with %s", self._client.__class__.__name__
        )
        return await self._client.async_process_audio_stream(metadata, stream)


class OpenAISTTEntity(SpeechToTextEntity):
    """OpenAI STT Entity for config entry support."""

    def __init__(
        self,
        config_entry: ConfigEntry,
        api_key: str,
        api_url: str,
        model: str,
        prompt: str,
        temperature: int,
        realtime: bool,
        noise_reduction: str,
    ) -> None:
        """Initialize OpenAI STT entity."""
        self._config_entry = config_entry
        self._api_key = api_key
        self._api_url = api_url
        self._model = model
        self._prompt = prompt
        self._temperature = temperature
        self._realtime = realtime
        self._noise_reduction = noise_reduction
        # Use the config entry title as the entity name
        self._attr_name = config_entry.title
        self._attr_unique_id = config_entry.entry_id

    @property
    def supported_languages(self) -> list[str]:
        """Return a list of supported languages."""
        return SUPPORTED_LANGUAGES

    @property
    def supported_formats(self) -> list[AudioFormats]:
        """Return a list of supported formats."""
        return [AudioFormats.WAV, AudioFormats.OGG]

    @property
    def supported_codecs(self) -> list[AudioCodecs]:
        """Return a list of supported codecs."""
        return [AudioCodecs.PCM, AudioCodecs.OPUS]

    @property
    def supported_bit_rates(self) -> list[AudioBitRates]:
        """Return a list of supported bitrates."""
        return [AudioBitRates.BITRATE_16]

    @property
    def supported_sample_rates(self) -> list[AudioSampleRates]:
        """Return a list of supported samplerates."""
        return [AudioSampleRates.SAMPLERATE_16000]

    @property
    def supported_channels(self) -> list[AudioChannels]:
        """Return a list of supported channels."""
        return [AudioChannels.CHANNEL_MONO]

    def _create_client(self):
        """Create and return the appropriate client based on configuration."""
        if self._realtime:
            # Use WebSocket client for OpenAI Realtime API
            return OpenAIWebSocketClient(
                async_get_clientsession(self.hass),
                self._api_key,
                self._api_url,
                self._model,
                self._prompt,
                self._noise_reduction,
            )

        # Use HTTP client for OpenAI Transcription API
        return OpenAIHTTPClient(
            async_get_clientsession(self.hass),
            self._api_key,
            self._api_url,
            self._model,
            self._prompt,
            self._temperature,
        )

    async def async_process_audio_stream(
        self, metadata: SpeechMetadata, stream: AsyncIterable[bytes]
    ) -> SpeechResult:
        """Process audio stream using the configured method (HTTP or WebSocket)."""
        client = self._create_client()
        _LOGGER.debug(
            "Processing audio stream with %s", client.__class__.__name__
        )
        return await client.async_process_audio_stream(metadata, stream)
