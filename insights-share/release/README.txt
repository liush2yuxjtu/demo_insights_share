insights-share v1.0.0 发布说明

这个目录现在具备两种发布方式：

1. 安装型发布
   在 insights-share/ 目录执行：
   python3 -m pip install .

   安装后可直接运行：
   insights-share --version
   insights-share serve --help

2. 压缩包发布
   在 insights-share/ 目录执行：
   python3 release/build_release.py

   默认会生成：
   dist/insights-share-v1.0.0.zip
   dist/insights-share-v1.0.0.zip.sha256
   dist/insights-share-v1.0.0.manifest.txt

压缩包会包含：
- demo_codes
- demo_docs
- validation
- VERSION
- pyproject.toml

压缩包不会包含：
- .env
- .venv
- __pycache__
- .pytest_cache
- .coverage
- 运行期生成的 wiki.json

推荐验收命令：
python3 -m pytest validation/test_release_package.py
bash demo_codes/run_demo.sh --no-ai
