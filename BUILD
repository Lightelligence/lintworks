py_library(
    name = "lintworks",
    srcs = [],
    deps = [
        "//lw:base",
        "//lw:linebase",
    ],
    visibility = ["//visibility:public"],
)    

py_test(
    name = "test_registry",
    srcs = ["tests/test_registry.py"],
    deps = [":lintworks"],
)
