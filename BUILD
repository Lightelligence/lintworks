py_library(
    name = "lib",
    srcs = [],
    deps = [
        "//lw:base",
        "//lw:linebase",
    ],
    visibility = ["//visibility:public"],
)    

py_binary(
    name = "main",
    srcs = ["main.py"],
    deps = [":lib"],
    visibility = ["//visibility:public"],
)    

py_test(
    name = "test_registry",
    srcs = ["tests/test_registry.py"],
    deps = [":lintworks"],
)


exports_files([
    "main.py",
])
