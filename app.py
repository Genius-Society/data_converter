import csv
import json
import gradio as gr
import pandas as pd
from utils import clean_dir, TMP_DIR, EN_US


MODE = {"from": "jsonl", "to": "csv"}
ZH2EN = {
    "模式": "Mode",
    "上传原数据": "Upload input file",
    "转换": "Convert",
    "下载转换数据": "Download output file",
    "数据预览": "Data viewer",
    "支持的 JSON 格式": "Supported JSON format",
    "支持的 JSON Lines 格式": "Supported jsonl format",
    "支持的 CSV 格式": "Supported CSV format",
    "状态栏": "Status",
    "# 数据文件转换": "# Data Format Converter",
}


def _L(zh_txt: str):
    return ZH2EN[zh_txt] if EN_US else zh_txt


def encoder_json(file_path: str):
    with open(file_path, "r", encoding="utf-8") as file:
        data_list = list(json.load(file))

    return data_list


def encoder_jsonl(file_path: str):
    data_list = []
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            # 加载每一行的 JSON 数据
            json_data = json.loads(line.strip())
            data_list.append(json_data)

    return data_list


def encoder_csv(file_path: str):
    data_list = []
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                data_list.append(dict(row))

    except UnicodeDecodeError:
        with open(file_path, "r", encoding="GBK") as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                data_list.append(dict(row))

    return data_list


def decoder_json(data_list: list, file_path: str):
    if data_list:
        with open(file_path, "w", encoding="utf-8") as file:
            # 将整个列表转换成 JSON 格式并写入文件
            json.dump(data_list, file, ensure_ascii=False, indent=4)

    return file_path


def decoder_csv(data_list: list, file_path: str):
    if data_list:  # 提取第一个字典的键作为表头
        header = list(data_list[0].keys())
        with open(file_path, "w", newline="", encoding="utf-8") as file:
            csv_writer = csv.writer(file)  # 写入表头
            csv_writer.writerow(header)  # 逐项写入字典的值
            for item in data_list:
                csv_writer.writerow([item[key] for key in header])

    return file_path


def decoder_jsonl(data_list: list, file_path: str):
    if data_list:
        with open(file_path, "w", encoding="utf-8") as file:
            for data in data_list:
                # 将每个 JSON 对象转换成字符串并写入文件，每行一个对象
                json_line = json.dumps(data, ensure_ascii=False)
                file.write(f"{json_line}\n")

    return file_path


def change_mode(input: str):
    global MODE
    affix = input.split(" ")
    if affix[1] == "→":
        MODE["from"] = affix[0]
        MODE["to"] = affix[2]

    else:
        MODE["from"] = affix[2]
        MODE["to"] = affix[0]


# outer func
def infer(input_file: str, cache=f"{TMP_DIR}/data"):
    status = "Success"
    output_file = previews = None
    try:
        clean_dir(cache)
        src_fmt = MODE["from"]
        dst_fmt = MODE["to"]
        data_list = eval(f"encoder_{src_fmt}")(input_file)
        output_file = eval(f"decoder_{dst_fmt}")(data_list, f"{cache}/output.{dst_fmt}")
        previews = pd.DataFrame(data_list)

    except Exception as e:
        status = f"{e}"

    return status, output_file, previews


if __name__ == "__main__":
    tab_cfgs = ["jsonl ⇆ csv", "json ⇆ csv", "json ⇆ jsonl"]
    with gr.Blocks() as data:
        gr.Markdown(_L("# 数据文件转换"))
        for item in tab_cfgs:
            types = item.split(" ⇆ ")
            with gr.Tab(item) as tab:
                with gr.Row():
                    with gr.Column():
                        option = gr.Dropdown(
                            choices=[
                                f"{types[0]} → {types[1]}",
                                f"{types[0]} ← {types[1]}",
                            ],
                            label=_L("模式"),
                            value=f"{types[0]} → {types[1]}",
                        )
                        input_file = gr.File(
                            type="filepath",
                            label=_L("上传原数据"),
                            file_types=[f".{types[0]}", f".{types[1]}"],
                        )
                        convert_btn = gr.Button(_L("转换"))

                    with gr.Column():
                        status_bar = gr.Textbox(label=_L("状态栏"), buttons=["copy"])
                        output_file = gr.File(type="filepath", label=_L("下载转换数据"))
                        data_viewer = gr.Dataframe(label=_L("数据预览"))

            option.change(change_mode, inputs=option)
            tab.select(change_mode, inputs=option)
            convert_btn.click(
                infer,
                inputs=input_file,
                outputs=[status_bar, output_file, data_viewer],
            )

        with gr.Row():
            with gr.Column():
                gr.Markdown(
                    f"""
                    ## {_L('支持的 JSON Lines 格式')}
                    ```
                    {{"key1": "val11", "key2": "val12", ...}}
                    {{"key1": "val21", "key2": "val22", ...}}
                    ...
                    ```    
                    ## {_L('支持的 CSV 格式')}
                    ```
                    key1, key2, ...
                    val11, val12, ...
                    val21, val22, ...
                    ...
                    ```
                    """
                )

            with gr.Column():
                gr.Markdown(
                    f"""
                    ## {_L('支持的 JSON 格式')}
                    ```
                    [
                        {{
                            "key1": "val11",
                            "key2": "val12",
                            ...
                        }},
                        {{
                            "key1": "val21",
                            "key2": "val22",
                            ...
                        }},
                        ...
                    ]
                    ```"""
                )

    data.launch(css="#gradio-share-link-button-0 { display: none; }")
