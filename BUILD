load("@com_github_bazelbuild_buildtools//buildifier:def.bzl", "buildifier")

buildifier(
    name = "buildifier_format_diff",
    diff_command = "diff",
    mode = "diff",
)

buildifier(
    name = "buildifier_lint",
    lint_mode = "warn",
    lint_warnings = [
        "-function-docstring-args",
        "-function-docstring",
    ],
    mode = "fix",
)

buildifier(
    name = "buildifier_fix",
    lint_mode = "fix",
    mode = "fix",
)

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
