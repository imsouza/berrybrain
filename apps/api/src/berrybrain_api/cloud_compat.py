"""Documented provider options for bounded, final-answer JSON requests."""

from urllib.parse import urlparse


def cloud_chat_options(endpoint: str, model: str) -> dict[str, object]:
    # Nemotron 3 otherwise spends the small JSON budget on reasoning and may
    # return no final content. Do not send NVIDIA extensions to other providers.
    if urlparse(endpoint).hostname == "integrate.api.nvidia.com" and model.startswith(
        "nvidia/nemotron-3"
    ):
        return {"chat_template_kwargs": {"enable_thinking": False}}
    return {}
