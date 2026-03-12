FROM python:3.11-slim

# 安裝中文字體（Noto Sans CJK，Google 開源字體，覆蓋繁體/簡體/日文/韓文）
RUN apt-get update && \
    apt-get install -y --no-install-recommends fonts-noto-cjk && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 安裝常用 Python 套件
RUN pip install --no-cache-dir \
    pandas \
    numpy \
    matplotlib \
    requests \
    openpyxl \
    scipy \
    scikit-learn \
    seaborn \
    Pillow \
    beautifulsoup4 \
    lxml \
    python-docx

# 設定 matplotlib 非互動後端
ENV MPLBACKEND=Agg

# 預設 matplotlib 使用 Noto Sans CJK 字體
RUN mkdir -p /home/sandbox/.config/matplotlib && \
    echo "font.family: Noto Sans CJK JP" > /home/sandbox/.config/matplotlib/matplotlibrc

# 建立非特權使用者
RUN useradd -m -s /bin/bash sandbox

# 清除 matplotlib 字體快取（確保重建時能找到新字體）
RUN python -c "import matplotlib; import shutil; shutil.rmtree(matplotlib.get_cachedir(), ignore_errors=True)"

# 建立工作目錄
RUN mkdir -p /workspace/output && chown -R sandbox:sandbox /workspace
RUN chown -R sandbox:sandbox /home/sandbox

# 切換到非特權使用者
USER sandbox
WORKDIR /workspace
