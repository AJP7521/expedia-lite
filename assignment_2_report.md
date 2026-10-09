## Research Notes

For my chatbot, I wanted something easy and convienient that the user could use. I originally used other chatbots like Amazon, Delta, and United to research. I wanted one response answers with the information available in the database, while also notifying the user if the information requested is not available. 

## Early Mockup/ Implementation

I unfortunatley did not take an image of the early mockup, however, I can describe it to the best of my ability. For starters, I used the link provided in the assignment to use the OpenRouter API key using the free Nemotron option. I copied and pasted the API key in the .env file, but it did not work at first. The reason for this is because the backend could not read the OpenRouter and it did not support JSON function. I made a new API key and this one worked successfully.

## Verification Record

For my verification checks, I used Boston because it has two hotels stored in the database. Prompting the chatbot with simple requests such as "What are the cheapest hotels in Boston" returned the two hotels stored in the database. I also prompted other zip codes to see if it would make up information, or return an error/ no information found result. I made sure the zip code finder from part 1 worked with the API key, and it did. For example I prompted for hotel costs in the zip code 23450 which is Virginia Beach. The prompt worked for Geoapify hotel finder, but it did not work for the chatbot. This makes sense because that information is not stored in the database for the controller to find. 

## AI Disclosure and Evidence Log

Attached is the first prompt I used to draft the chatbot: 

Supply a plan for an AI chatbot for Expedia Lite. The user should be able to ask open-ended questions about the database. The frontend must show text input for the user's question, a submit/ send button, a loading state while the request is being processed, the final answer, a clear failure or error message, a clear answer for no matching records exist, a clear message where there is insufficient data. The backend must implement the chatbot using a two-step LLM process. The LLM must never directly connect or access SQLite. The backend receives the proposed SQL and validate it before execution. Do not implement anything but show me a plan. Stop.

Attached is the prompt I used for verifying and troubleshooting the new Nemotron API key through OpenRouter:

I added the OpenRouter API key. Verify that it works. Stop.

The OpenRouter key is valid: authentication returned HTTP 200.
However:
- The test AI request returned HTTP 402 (Payment Required).
- Expedia Lite still targets OpenAI and does not read OPENROUTER_API_KEY, so it needs an OpenRouter integration change.
No files or data were changed. Stopped.

why does the key not work?

The key itself works—it authenticated successfully. Two separate issues prevent chatbot answers:
1. OpenRouter rejected the test generation with HTTP 402 (Payment Required). Check your OpenRouter credit balance and the key’s spending limit. Authentication can succeed even when paid model requests are blocked.
2. The chatbot currently connects to OpenAI, not OpenRouter. It reads OPENAI_API_KEY; your OPENROUTER_API_KEY is not used.
The backend needs OpenRouter support, and the selected model needs sufficient credits or an available free option.

## Solution

I went back to the OpenRouter website to troubleshoot and realized the API key usage limit was set to zero. I quickly changed this and restarted Codex, and it worked. 

## Video of Chatbot

https://github.com/AJP7521/expedia-lite/blob/1ef1b5c6c8fbf87cc43c2e645560c3e9ab685622/Video%20Demo%203.mov
