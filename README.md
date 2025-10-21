# OpenAI Speech-To-Text for Home Assistant

This custom component integrates [OpenAI Speech-to-Text](https://platform.openai.com/docs/guides/speech-to-text), also known as Whisper, into Home Assistant via the OpenAI API for use in the Assist pipeline.

## Installation

### HACS (Recommended)


This integration is part of the standard HACS repository. Just search for "OpenAI Whisper API" to install it, or use this link to go directly there:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=einToast&repository=openai_stt_ha&category=integration)


### Manual

1. Inside your `config` directory, create a new directory named `custom_components`
2. Create a new directory named `openai_stt` inside the `custom_components` directory
3. Place all the files from this repository in the `openai_stt` directory
4. Restart Home Assistant

## Configuration

You need to create an account on the [OpenAI website](https://platform.openai.com/signup) and get an [API key](https://platform.openai.com/api-keys).

### UI Configuration (Recommended)

Starting with version 1.3.0, this integration supports full UI-based configuration through Home Assistant's integrations page.

1. Go to **Settings** > **Devices & Services**
2. Click on **+ Add Integration**
3. Search for "OpenAI Whisper API" or "OpenAI STT"
4. Enter your OpenAI API key and configure the optional settings
5. Click **Submit** to complete the setup

You can modify settings later by clicking **Configure** on the integration card.

### YAML Configuration (Legacy)

For backward compatibility, YAML configuration is still supported. Add the following to your `configuration.yaml` and restart Home Assistant:

```yaml
stt:
  - platform: openai_stt
    api_key: YOUR_API_KEY
    #  Optional parameters
    realtime: false
    api_url: https://api.openai.com/v1
    model: gpt-4o-mini-transcribe
    prompt: ""
    temperature: 0
    noise_reduction: null
```

**Note:** It's recommended to migrate to UI configuration for a better experience and easier management.

### Configuration Parameters:

- `api_key` (Required): Your OpenAI API key
- `api_url` (Optional): The API URL to use. Specify this to use any compatible OpenAI API. The default is `https://api.openai.com/v1`.
- `model` (Optional): The model to use. Currently, the [supported models](#supported-models) are `gpt-4o-mini-transcribe`, `gpt-4o-transcribe` and `whisper-1`. The default is `gpt-4o-mini-transcribe`. All available models are listed in the [OpenAI model list](https://platform.openai.com/docs/models) under the Transcription section
- `prompt` (Optional): The prompt to use. The default is an empty string. See the [OpenAI documentation](https://platform.openai.com/docs/guides/speech-to-text#prompting) for more information
- `temperature` (Optional): The temperature to use between `0` and `1`. A higher temperature will make the model more creative, but less accurate. The default is `0`. Only applicable when `realtime: false`
- `realtime` (Optional): If set to `true`, the integration will use the OpenAI Realtime API. This should generate faster results. If set to `false`, the integration will use the regular OpenAI Transcription API. The default is `false`. Keep in mind that the Realtime API is currently in beta and may not be as stable as the Transcription API. See the [OpenAI documentation](https://platform.openai.com/docs/guides/realtime-transcription) for more information
- `noise_reduction` (Optional): The noise reduction to use. The available options are `null`, `near_field` and `far_field`. `near_field` is for close-range audio, `far_field` is for distant audio, `null` turns off noise reduction. The default is `null`. Only applicable when `realtime: true`

## Supported Models
See the accuracy comparison of the models [here](https://openai.com/index/introducing-our-next-generation-audio-models/).

- `gpt-4o-mini-transcribe`: model optimized for speed and cost. Cost: estimated `$0.003` per minute of audio
- `gpt-4o-transcribe`: model optimized for accuracy. Cost: estimated `$0.006` per minute of audio
- `whisper-1`: original `whisper-large-v2` model. Superseded by `gpt-4o-mini-transcribe` and `gpt-4o-transcribe`. Cost: `$0.006` per minute of audio

## Migration from YAML to UI Configuration

If you're currently using YAML configuration and want to migrate to the UI:

1. Go to **Settings** > **Devices & Services**
2. Click on **+ Add Integration**
3. Search for "OpenAI Whisper API"
4. Enter your configuration settings in the UI
5. Once confirmed working, remove the YAML configuration from `configuration.yaml`
6. Restart Home Assistant

## Troubleshooting

If you encounter issues:

1. Check that your API key is valid and has sufficient credits
2. Verify the API URL is correct (default: `https://api.openai.com/v1`)
3. Check Home Assistant logs for detailed error messages
4. Ensure you're using a supported model

For YAML configuration users: If you see an error message about "stt integration does not support any configuration parameters", this is a known [bug](https://github.com/home-assistant/core/issues/97161) in some Home Assistant versions. The error message can be safely ignored, or you can migrate to UI configuration to avoid it.