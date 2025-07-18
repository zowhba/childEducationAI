import json

panel_files = [
    ("result_error_code_status.json", "extract_error_code_status.json"),
    ("result_response_code_status.json", "extract_response_code_status.json"),
    ("result_model_status.json", "extract_model_status.json"),
    ("result_server_status.json", "extract_server_status.json"),
]

def extract_result(result_json_path, output_json_path):
    with open(result_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    frames = data["results"]["A"]["frames"]
    result_dict = {}
    for frame in frames:
        name = frame["schema"]["name"]
        times = frame["data"]["values"][0]
        values = frame["data"]["values"][1]
        series = [
            {"timestamp": t, "value": v}
            for t, v in zip(times, values)
        ]
        result_dict[name] = series
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(result_dict, f, ensure_ascii=False, indent=2)
    print(f"{output_json_path} 파일로 저장 완료!")

def main():
    for result_file, output_file in panel_files:
        extract_result(result_file, output_file)

if __name__ == "__main__":
    main() 