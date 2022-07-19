py_library(
    name = "lib",
    srcs = [],
    visibility = ["//visibility:public"],
    deps = [
        "//lw:base",
        "//lw:linebase",
    ],
)

py_binary(
    name = "main",
    srcs = ["main.py"],
    visibility = ["//visibility:public"],
    deps = [":lib"],
)

exports_files([
    "main.py",
])
