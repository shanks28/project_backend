# import os
# from langchain.llms import OpenAI
# from langchain.chains import LLMChain
# from transformers import BartForConditionalGeneration, BartTokenizer
# model_name='facebook/bart-large'
# tokenizer=BartTokenizer.from_pretrained(model_name)
# model=BartForConditionalGeneration.from_pretrained(model_name)
# prompt="A long-term investment strategy entails holding investments for more than a full year. This strategy includes holding assets like bonds, stocks, exchange-traded funds (ETFs), mutual funds, and more. It requires discipline and patience to take a long-term approach. That's because investors must be able to take on a certain amount of risk while they wait for higher rewards down the road.\n\nInvesting in stocks and holding them is one of the best ways to grow wealth over the long term. For example, the S&P 500 experienced annual losses in only 13 of the last 50 years, dating back to 1974, demonstrating that the stock market generates returns much more often than it doesn't.\n\nKey Takeaways Long-term stock investments tend to outperform shorter-term trades by investors attempting to time the market.\n\nEmotional trading tends to hamper investor returns.\n\nThe S&P 500 posted positive returns for investors over most 20-year time periods.\n\nRiding out temporary market downswings is often considered a sign of a good investor.\n\nInvesting long term cuts down on costs and allows you to compound any earnings you receive from dividends.\n\nBetter Long-Term Returns\n\nThe term asset class refers to a specific category of investments. They share the same characteristics and qualities, such as fixed-income assets (bonds) or equities, which are commonly called stocks. The asset class that's best for you depends on several factors, including your age, risk profile and tolerance, investment goals, and the amount of capital you have. But which asset classes are best for long-term investors?\n\nIf we look at several decades of asset class returns, we find that stocks have generally outperformed almost all other asset classes. The S&P 500 returned a geometric average of 9.80% per year between 1928 and 2023. This compares favorably to the 3.30% return of three-month Treasury bills (T-bills), the 4.86% return of 10-year Treasury notes, and the 6.55% return of gold, to name a few.\n\nEmerging markets have some of the highest return potentials in the equity markets, but also carry the highest degree of risk. This class historically earned high average annual returns but short-term fluctuations have impacted their performance. For instance, the 10-year annualized return of the MSCI Emerging Markets Index was 2.66% as of Dec. 29, 2023.\n\nSmall and large caps have also delivered above-average returns. For instance, the 10-year return for the Russell 2000 index, which measures the performance of 2,000 small companies, was 7.08% as of Jan. 26, 2024."
# inputs=tokenizer.encode(prompt,return_tensors='pt',max_length=512)
# outputs=model.generate(inputs,max_length=512,num_beams=5,early_stopping=True)
# repurposed_text=tokenizer.decode(outputs[0],skip_special_tokens=True)
# print(repurposed_text)
from dotenv import load_dotenv
load_dotenv()
import os
api_key=os.getenv("API_KEY")
import httpx
