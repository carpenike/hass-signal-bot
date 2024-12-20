# Changelog

## 1.0.0 (2024-12-20)


### Features

* add additional constants to the const.py file. ([cb6e771](https://github.com/carpenike/hass-signal-bot/commit/cb6e77195313763eced33b386827ca54a8e6e35e))
* add basic group management for receiving and sending ([f05c442](https://github.com/carpenike/hass-signal-bot/commit/f05c442cd0b690e64f95a166ad70c79e68a64d61))
* add group information for messages being added to sensor ([37d261e](https://github.com/carpenike/hass-signal-bot/commit/37d261ea989991c6ba24b59b32cef27ea035321f))
* add group information to latest_message if message came from group ([c3b4ff4](https://github.com/carpenike/hass-signal-bot/commit/c3b4ff41a679384ab6d5a827b253f96174997ecc))
* add group membership information to the message if message comes from group ([78490a6](https://github.com/carpenike/hass-signal-bot/commit/78490a69d0a8b383d5eb1e5d07d4d8f5f05d0649))
* initial add of changelog file that will be managed by release-please ([1ce41bd](https://github.com/carpenike/hass-signal-bot/commit/1ce41bd5c8378d50d7df20a99322b3e220ee30f7))
* move CI to use pre-commit rather than individual steps for ruff / black ([8f2bda8](https://github.com/carpenike/hass-signal-bot/commit/8f2bda8416a3785480a5a088ae84c5698f02ac24))
* update __init__.py to leverage new constants and be more consistent. ([c3dab65](https://github.com/carpenike/hass-signal-bot/commit/c3dab656290f48dcd496cff50fbd2163d83350be))
* update config_flow.py to make use of the new const.py options ([64cb6fc](https://github.com/carpenike/hass-signal-bot/commit/64cb6fc18b7868055f7c265fedf12bcee4dd78b1))
* update lint tools and consolidate workflows ([8ca12bc](https://github.com/carpenike/hass-signal-bot/commit/8ca12bc32d894183032f3df4dfafc4379bbdb48f))
* update release-please to only trigger a release update if changes are made to custom_components directory ([62d7e0c](https://github.com/carpenike/hass-signal-bot/commit/62d7e0c9a582651add48cad92158b1fe4d98fc0c))
* update sensor.py to use new const.py values, and also support the proper group lookups. ([6f76a80](https://github.com/carpenike/hass-signal-bot/commit/6f76a809a89b364ec53b958b6fca2cba16b9766f))
* update signal_websocket.py to use more of the constants for consistency. ([c869c41](https://github.com/carpenike/hass-signal-bot/commit/c869c419268cff0db5882105c260b0b39e224f95))
* update utils.py to make use of constants ([e60ccce](https://github.com/carpenike/hass-signal-bot/commit/e60cccee3076bcb045572ee4d88fd056d5d63707))


### Bug Fixes

* add additional logging to the group messages to figure out why we're not updating group attributes ([dbbf14a](https://github.com/carpenike/hass-signal-bot/commit/dbbf14a5cd2f1c28ec1278d3a57242f0d9bafa05))
* add additional string descriptors for the setup workflow ([7cf675c](https://github.com/carpenike/hass-signal-bot/commit/7cf675c27842ade9082c1f4d36fbd12ac51b9a31))
* ci was failing due to pyproject formatting. attempting to resolve. Updated ruff version in workflow ([d68437c](https://github.com/carpenike/hass-signal-bot/commit/d68437ca353b8b05fd65987dc8a3a70bc004563a))
* let's try running ruff after installing it instead of using the native action ([b843d86](https://github.com/carpenike/hass-signal-bot/commit/b843d86a173968bf6113008994704ff6f57443ac))
* lint updates ([a405aad](https://github.com/carpenike/hass-signal-bot/commit/a405aad4d252cdc1b0284cf8f0e278b555d0d108))
* lint updates, file had lines too long ([197cb33](https://github.com/carpenike/hass-signal-bot/commit/197cb3300557542071bbf3c8798b0ececd775f9f))
* make en.json consistent in format with strings.json ([92a45a9](https://github.com/carpenike/hass-signal-bot/commit/92a45a9f23385d4617922c0a5a9dac391ae33971))
* move to chartboost instead of astral for now ([7d8794a](https://github.com/carpenike/hass-signal-bot/commit/7d8794a36b41398d5d66f730ec48fa5a9e43f582))
* move to our defined CONF_API_URL value instead of coming from hass ([fe0b760](https://github.com/carpenike/hass-signal-bot/commit/fe0b760ce191873760e9621f01199f94a3dc7686))
* need to properly match the internal_id from the /v1/receive api and match it to internal_id from the group api ([495034f](https://github.com/carpenike/hass-signal-bot/commit/495034fb8c976dc11fe83adc430f3f950d6184ed))
* nest the toml config more ([c359a02](https://github.com/carpenike/hass-signal-bot/commit/c359a02d54e4adcc2d04e62db1bd9d0affece3c3))
* pass lint checks from pre-commit ([f279a85](https://github.com/carpenike/hass-signal-bot/commit/f279a85747afbcd8539a109d5a6953303bbfcbe6))
* pre-commit was adding prettier which is unneeded. removed. ([d7e6786](https://github.com/carpenike/hass-signal-bot/commit/d7e6786475a6d7c7a4c6af5c14cc0fb48262e47b))
* properly pick the group api and key ([ff4bfb6](https://github.com/carpenike/hass-signal-bot/commit/ff4bfb6b0b0a4974f483e1a2d7fa213d1eb6b538))
* remove sections call out as it was breaking the ci jobs ([5e676f1](https://github.com/carpenike/hass-signal-bot/commit/5e676f158d0237ab7be76e35ca67fa67d06fa26c))
* remove whitespace in the pyproject.toml file ([54f8e45](https://github.com/carpenike/hass-signal-bot/commit/54f8e456fbdbfeb9dcb7a6b6d381f22f6d019e8b))
* resolve issue with trying to update a read-only dict from hass ([4afae22](https://github.com/carpenike/hass-signal-bot/commit/4afae222d72994361d51e8b9a7d60d9cb282203a))
* resolve issues with unavailable event loop for async callbacks ([60974b4](https://github.com/carpenike/hass-signal-bot/commit/60974b4a5e3aa99e033ab0a7454def0bf132cfe5))
* sensor.py updated to meet ruff lint guidelines ([38c23b6](https://github.com/carpenike/hass-signal-bot/commit/38c23b60a69977fb3dfb5acc4ce0a6d61b5b3700))
* update __init__.py to meet ruff lint guidelines ([3db714c](https://github.com/carpenike/hass-signal-bot/commit/3db714c33745ab67c8552e249f812186922d3313))
* update a string to match what's in the en.json ([2c61de9](https://github.com/carpenike/hass-signal-bot/commit/2c61de94d66f3637d1a99bda28410cb73fda96c9))
* update ci image files and pin to sha versions ([f357e4a](https://github.com/carpenike/hass-signal-bot/commit/f357e4ac31e34ab7d71d26d688d2ecf72bc8fd8c))
* update config_flow.py to meet ruff lint guidelines ([1a276ae](https://github.com/carpenike/hass-signal-bot/commit/1a276aecdb03e3975ddf9b4546e92bee7eb2d76e))
* update en.json to reflect what's in strings.json ([6fb0386](https://github.com/carpenike/hass-signal-bot/commit/6fb038604bba5f5b656500abf48ae80fa319f6d0))
* update files to use the correct api_endpoint_receive variable ([967dc56](https://github.com/carpenike/hass-signal-bot/commit/967dc5662a2834feb7cb5bee193a1244e4161531))
* update group collection process to make sure we're grabbing relevant group info for group messages ([05b9a18](https://github.com/carpenike/hass-signal-bot/commit/05b9a18ba970eaefa453357f31dc723dda512bbd))
* update metadata required by hacs ([2684ac9](https://github.com/carpenike/hass-signal-bot/commit/2684ac9e39c77f195fc7c2d43ddbe672301ba68a))
* update renovate config so commits will show up in changelog properly ([418bc3e](https://github.com/carpenike/hass-signal-bot/commit/418bc3e33af9198fb51f51fb33990bf7cf6f2c01))
* update renovate schedule to not use weekly ([9ac903c](https://github.com/carpenike/hass-signal-bot/commit/9ac903c4a103750b21ce3e3885e427fe9e616e4e))
* update send response to accept a 201 for successful message ([20fd80e](https://github.com/carpenike/hass-signal-bot/commit/20fd80e087d40b031a4a0eefe0b06f5a60667bac))
* update signal_websocket.py to work with ruff ([3029de8](https://github.com/carpenike/hass-signal-bot/commit/3029de895a5c82cec89624a4452a01e9c8d8e1e9))
* update to meet hassfest format requirements ([4678539](https://github.com/carpenike/hass-signal-bot/commit/4678539ef4869ec7bf039eeebed31bba0f4593b6))
* update to meet hassfest requirements ([ea58f86](https://github.com/carpenike/hass-signal-bot/commit/ea58f86c1f53a028e1edc0d39506dae211941adf))
* update utils.py to meet ruff lint guidelines ([63e4703](https://github.com/carpenike/hass-signal-bot/commit/63e47032a9a7c15bc0284107fc763c03bbc188e4))
* update vscode extension to use ruff configuration for linting ([0414b9c](https://github.com/carpenike/hass-signal-bot/commit/0414b9cc942eaff6a63a639d44c901383197a6f1))
* workflow wasn't expecting a sequence ([a15e3be](https://github.com/carpenike/hass-signal-bot/commit/a15e3bef6e4cefd1f2f9261faa538cdc8ac9dbd7))

## Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
