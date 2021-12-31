import logging

import artifactoryconfig.lib.namespaces as namespaces


def test_add_markdown_unique_patterns(caplog):
    caplog.set_level(logging.INFO)
    namespaces_markdown = []
    namespace_with_duplicate_patterns = namespaces.Namespace({"name": "namespace1"})
    namespace_with_duplicate_patterns.public_patterns = ["duplicate-pattern.*"]
    namespace_with_duplicate_patterns.internal_patterns = ["duplicate-pattern.*"]

    namespaces.add_markdown_row(namespace_with_duplicate_patterns, namespaces_markdown)

    assert ("| namespace1 | duplicate-pattern.\\* |" in namespaces_markdown)
