from transformers import T5Tokenizer, T5ForConditionalGeneration
from langchain.prompts import PromptTemplate
import torch
from langchain.llms import HuggingFaceHub
from langchain.chains import LLMChain

model_path = "./fine_tuned_model"
tokenizer = T5Tokenizer.from_pretrained(model_path)
model = T5ForConditionalGeneration.from_pretrained(model_path)
model.eval()  # turn off backpropagation

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)

prompt_template = PromptTemplate(
    template="Your task is to rephrase {content} to match what would generally be used on the platform {platform}",
    input_variables=["platform", "content"]
)

def generate_text(prompt):
    input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(device)
    outputs = model.generate(input_ids, max_length=512)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

class CustomLLM(HuggingFaceHub):
    def _call(self, prompt, stop=None):
        return generate_text(prompt)

llm = CustomLLM()
chain = LLMChain(prompt=prompt_template, llm=llm)

inputs_variables = {
    "platform": "beehive",
    "content": "Social media marketing is essential for brand growth. Here are five tips to boost your social media presence: 1. Post consistently, 2. Engage with your audience, 3. Use hashtags effectively, 4. Collaborate with influencers, 5. Analyze your performance"
}

response = chain.run(inputs_variables)
print(response)