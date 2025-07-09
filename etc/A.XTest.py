from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_name = "skt/A.X-4.0"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.bfloat16, device_map="auto")
model.eval()

input_ids = tokenizer("안녕하세요, 한국어 성능 테스트입니다.", return_tensors="pt").to(model.device)
out = model.generate(input_ids.input_ids, max_new_tokens=100)
print(tokenizer.decode(out[0], skip_special_tokens=True))
