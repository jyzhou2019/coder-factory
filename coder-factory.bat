@echo off
REM Coder-Factory Windows Runner
REM Usage: coder-factory <command> [args]

docker run --rm -it ^
    -v "%CD%:/workspace" ^
    -w /workspace ^
    coder-factory:latest %*
