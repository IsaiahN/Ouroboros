> ## Documentation Index
> Fetch the complete documentation index at: https://docs.arcprize.org/llms.txt
> Use this file to discover all available pages before exploring further.

# Render Games

> How to render ARC-AGI-3 games

You can render games in several ways:

## Terminal Rendering (bounded)

Text-based rendering with frame rate limiting:

```python  theme={null}
env = arc.make("ls20", render_mode="terminal")
```

## Terminal Rendering (unbounded)

Text-based rendering without frame rate limiting:

```python  theme={null}
env = arc.make("ls20", render_mode="terminal-fast")
```

## Human Rendering

Matplotlib visualization with frame rate limiting:

```python  theme={null}
env = arc.make("ls20", render_mode="human")
```

## Custom Renderer

Provide your own rendering function:

```python  theme={null}
from arcengine import FrameDataRaw

def my_renderer(steps: int, frame_data: FrameDataRaw) -> None:
    print(f"Step {steps}: {frame_data.state.name}")

env = arc.make("ls20", renderer=my_renderer)
```
