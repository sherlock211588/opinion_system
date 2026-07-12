import os
from modelscope.hub.snapshot_download import snapshot_download

# 定位项目根目录
script_abs = os.path.abspath(__file__)
project_root = os.path.dirname(script_abs)

# 统一存放路径
save_dir = os.path.join(project_root, "models", "yangjiurong", "chinese-sentiment-c3-v1")
os.makedirs(save_dir, exist_ok=True)

model_id = "yangjiurong/chinese-sentiment-c3-v1"

# 删除不兼容参数 local_dir_use_symlinks
model_dir = snapshot_download(
    model_id=model_id,
    local_dir=save_dir
)

print(f" 模型下载完成，本地路径：{model_dir}")