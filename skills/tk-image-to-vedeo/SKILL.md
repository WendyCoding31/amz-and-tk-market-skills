---
name: tk-image-to-vedeo
description: Create TikTok Shop style product short videos from one required product image or TikTok product clue using an agent's own vision capability plus a bundled Seedance CLI. Use when the user asks to generate TK/TikTok product videos, TikTok Shop product display videos, UGC-style ecommerce videos, product image-to-video, product ad creatives, or TK short videos with chosen aspect ratio, duration, resolution, and audio mode.
---

# TK Image to Vedeo

This skill turns one product image or TikTok Shop product clue into a TikTok-ready product short video. It is agent-agnostic: use the executing agent's own image understanding and any available TikTok product facts; do not call or assume Codex/OpenAI vision APIs.

Use this skill for rendering a short video with Seedance. If the user only wants TikTok content strategy, hooks, captions, or creator briefs without rendering, use `tk-video-script` instead.

## Required Inputs

Stop and ask for missing inputs before analysis or generation:

- exactly one primary product image, as an uploaded image, local path, public URL, or `asset://...` URI
- video aspect ratio, usually `9:16` for TikTok; supported values include `9:16`, `1:1`, `3:4`, `4:3`, `16:9`, or `21:9`
- video duration
- resolution, `720p` or `1080p`
- audio preference, either `silent` or `generate_audio`

Optional:

- TikTok Shop product link, `commodityId`, title, price, category, market, or target language
- short selling-point description from the user
- target angle, such as UGC demo, problem-solution, creator ad, comparison, unboxing, or benefit proof
- model preference; default is `seedance-2`

## Hard Gate

Never call Seedance before the user chooses one script and confirms the final render summary with the estimated cost.

The first response for a new run must:

1. analyze the image and product clue
2. write 3 candidate TikTok scripts
3. save the scripts to `scripts.json`
4. save a user-readable version to `script_cards.md`
5. display the detailed description of all 3 scripts in the chat
6. stop and ask the user to choose `1`, `2`, or `3`

After the user chooses one script, the next response must:

1. save `selected_script.json`
2. save `render_plan.json`
3. display a final render summary in the chat
4. display the estimated credit and CNY cost
5. stop and ask the user to explicitly confirm generation

Only after the user explicitly confirms the final render summary may you run `scripts/seedance_video.py submit`.

The confirmation summary must include:

- selected script name
- aspect ratio, duration, resolution, model
- audio mode (`silent` or `generate_audio`)
- output folder
- estimated credits and CNY cost
- whether the request will use `--no-audio` or `--generate-audio`

Cost estimate rules:

- Use `seedance-2` 720p: `28.57` credits/s.
- Use `seedance-2` 1080p: `71.43` credits/s.
- Use `0.035` CNY/credit.
- Estimated CNY = `credits_per_second * duration_seconds * 0.035`.
- If the selected model/resolution has no known rate, show `cost unknown` and ask for confirmation before submitting.

## Workflow

### 1. Create the run folder

Use a timestamped folder unless the user specifies a folder:

```bash
mkdir -p ~/Desktop/tk-image-to-vedeo-output/$(date +%Y%m%d-%H%M%S)
```

Save all run artifacts there by default, including analysis files, script files, request/result JSON files, and downloaded videos.

### 2. Analyze the product and TikTok context

Use your own image recognition capability and the optional product clue. Do not infer unsupported product facts.

If the user provides a TikTok Shop link, `commodityId`, keyword, or category and TikTok MCP/openboost tools are available, gather product facts and content signals before writing scripts. If those tools are unavailable, proceed only with the user-provided facts and mark missing evidence clearly.

Save `analysis.json` with this structure:

```json
{
  "image": "path-or-url",
  "product_clue": "optional TikTok link, commodityId, title, keyword, or category",
  "market": "optional market/language, default US/English if unspecified",
  "user_description": "optional user text",
  "visible_product_facts": ["facts directly visible in the image"],
  "confirmed_selling_points": ["safe benefits supported by image, user text, or TikTok data"],
  "tiktok_signals": ["observed product, video, creator, comment, or sales-channel signals"],
  "uncertain_observations": ["possible but unverified observations"],
  "do_not_claim": ["claims the video prompt must avoid"],
  "tk_style_notes": ["short-form, UGC-like, mobile-first display guidance"]
}
```

Rules:

- Keep physical facts conservative: visible material, color, shape, count, texture, packaging, and use context.
- Treat size, capacity, compatibility, certifications, waterproofing, medical effects, safety claims, discounts, scarcity, and performance claims as unknown unless the user or data provides them.
- TikTok style means mobile-first vertical framing, a concrete first-3-second visual hook, natural use context, quick product proof, and restrained benefit language.
- Avoid hard text overlays inside the Seedance prompt unless the user explicitly wants generated on-video text. Prefer leaving space for captions/subtitles to be added later.

### 3. Generate 3 scripts

Create exactly 3 TikTok-ready scripts:

1. UGC problem-solution script
2. Fast demo / proof script
3. Creator-style product ad script

Each script must include:

- `id`: `1`, `2`, or `3`
- `name`
- `positioning`
- `target_viewer`
- `first_3_seconds_hook`
- `scene_plan`: 3-6 short beats with timing notes
- `caption_plan`: short subtitles or caption intent, not necessarily baked into the generated video
- `audio_direction`: silent-safe direction or generated-audio direction
- `seedance_prompt`: one final video-generation prompt ready for Seedance
- `why_this_script`
- `evidence_used`: image facts, user facts, or TikTok data used
- `risk_notes`: unsupported claims to avoid

Save them to `scripts.json`.

Then, in the same chat response, show all 3 script options in a user-readable format so the user does not need to open the JSON file. For each script, include:

- script number and `name`
- `positioning`
- `target_viewer`
- full `scene_plan` with timing notes
- first-3-second hook
- visual focus, caption direction, and recommended audio direction
- a concise version of `why_this_script`
- key `risk_notes`

Do not paste the full `seedance_prompt` by default unless the user asks to inspect prompts. Keep the chat version detailed enough for the user to compare and choose, but easier to scan than raw JSON.

Also save this chat-friendly version to `script_cards.md`.

After displaying the 3 detailed script descriptions, stop and ask the user to choose `1`, `2`, or `3`. Do not choose automatically.

### 4. Confirm the selected render plan

After the user chooses a script:

1. Save `selected_script.json`.
2. Save `render_plan.json` with the selected script, final prompt, image path, aspect ratio, duration, resolution, model, audio mode, output folder, and cost estimate.
3. Display the final render summary and cost estimate in the chat.
4. Stop and wait for explicit user confirmation before submitting.

If the user chose `silent`, the prompt may include `silent video` and the CLI must use `--no-audio`.
If the user chose `generate_audio`, the prompt must describe the desired music, ambient sound, or creator-ad energy and must not include `silent video`; the CLI must use `--generate-audio`.

### 5. Generate the selected video

After the user confirms the render plan:

1. Use the product image as `--first-frame`.
2. Use the selected script's final prompt as `--prompt`.
3. Pass the user's aspect ratio, duration, resolution, and model.
4. Pass `--no-audio` or `--generate-audio` exactly as confirmed.
5. Use `--wait --download` when the user expects the final video now.

Example:

```bash
python3 scripts/seedance_video.py submit \
  --prompt "TikTok Shop vertical product video, UGC-style handheld demo, strong first 3 seconds, product clearly visible, realistic home use scene, quick close-up proof, natural lighting, leave clean space for captions, no exaggerated claims." \
  --first-frame ./product.png \
  --aspect-ratio 9:16 \
  --duration 8 \
  --resolution 720p \
  --no-audio \
  --wait \
  --download \
  --output-dir ~/Desktop/tk-image-to-vedeo-output/20260615-160000
```

The bundled CLI writes:

- `seedance_request.json`
- `result.json`
- `run_manifest.json`
- downloaded `.mp4` when `--download` is used and the task completes

After generation, inspect the downloaded video with `ffprobe` when available and report:

- local `.mp4` path
- duration
- resolution
- whether an audio stream exists
- actual status and task id

## Seedance CLI

The skill is self-contained and includes `scripts/seedance_video.py`.

Configuration:

- Never hardcode API keys in skill files, scripts, examples, or user-facing output.
- The CLI reads `VIDEO_API_KEY` and `VIDEO_API_BASE_URL` from the environment or local env files.
- Local image paths are uploaded to the configured compatible API first with `/v1/uploads/images`; the returned URL is then used in the video request because generation endpoints may reject base64 image data.
- Preferred env file: `~/.config/tk-image-to-vedeo/env`
- Compatible fallback: `~/.config/amz-image-to-vedeo/env`
- Compatible fallback: `~/.config/seedance-video/env`

Useful commands:

```bash
python3 scripts/seedance_video.py config-check
```

```bash
python3 scripts/seedance_video.py estimate-cost \
  --model seedance-2 \
  --duration 8 \
  --resolution 1080p
```

```bash
python3 scripts/seedance_video.py submit \
  --prompt "..." \
  --first-frame ./product.png \
  --aspect-ratio 9:16 \
  --duration 8 \
  --resolution 720p \
  --no-audio \
  --dry-run
```

## Failure Handling

- Missing product image: stop and request one image.
- Missing aspect ratio, duration, or resolution: stop and request the missing settings.
- More than one product image: ask which single image should be the first frame.
- User has not chosen a script: stop; do not call Seedance.
- User has not chosen `silent` or `generate_audio`: stop; do not call Seedance.
- User has not confirmed the render summary and estimated cost: stop; do not call Seedance.
- TikTok data is unavailable: continue with image/user-provided facts only and mark missing evidence.
- Seedance returns `failed`: report `error.code` and `error.message`, and keep all saved artifacts.
- Video URL expires: download immediately when possible and return the local `.mp4` path.
