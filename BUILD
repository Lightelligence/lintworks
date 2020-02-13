py_library(
    name = "lintworks",
    srcs = [
        "lintworks/base.py",
        "lintworks/linebase.py",
    ],
)

py_test(
    name = "test_registry",
    srcs = ["tests/test_registry.py"],
    deps = [":lintworks"],
)
