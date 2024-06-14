from datasets import load_dataset
from transformers import T5Tokenizer, T5ForConditionalGeneration,TrainingArguments,Trainer # uses pytorch internally
import torch
dataset=load_dataset('paws','labeled_final')
tokenizer=T5Tokenizer.from_pretrained('t5-small')
model=T5ForConditionalGeneration.from_pretrained('t5-small')
device=torch.cuda.is_available()
torch.cuda.empty_cache()
def tokenize(text):
    inputs=["paraphrase: "+ i for i in text['sentence1']]
    model_inputs=tokenizer(inputs,max_length=128,padding="max_length",truncation=True,return_tensors="pt")
    with tokenizer.as_target_tokenizer():
        labels=tokenizer(text['sentence2'],max_length=512,padding="max_length",truncation=True,return_tensors="pt") # already paraphrased text for the text in sentence1
    model_inputs['labels']=labels['input_ids']
    return model_inputs
tokenized_dataset=dataset.map(tokenize,batched=True)
training_args=TrainingArguments(output_dir='./fine_tuned_model',
                                evaluation_strategy='epoch',
                                learning_rate=3e-2,
                                per_device_train_batch_size=4,
                                per_device_eval_batch_size=4,
                                num_train_epochs=2,
                                use_cpu=not device,
                                save_strategy='no')
trainer=Trainer(args=training_args, train_dataset=tokenized_dataset['train'],
                model=model,eval_dataset=tokenized_dataset['validation'],)
trainer.train()
eval_results=trainer.evaluate()
model.save_pretrained('./fine_tuned_model')
tokenizer.save_pretrained('./fine_tuned_model')

# if __name__=="__main__":
#     print(dataset)