# HayPoll
because hay > straw

## Setup Instructions
This is a facebook bot that can help you to create surveys, which others can respond through the bot.

Installing requirements:
`pip3 install -r requirements.txt`

Create a Facebook Page for your application, and create an application for your page. Setup your tokens when you create the messenger applications as well. This can be done through the [FaceBook Developers page](https://developers.facebook.com/apps/). 

To create this application, create a file called keys.py with ACCESS_TOKEN and VERIFY_TOKEN (for used for the webhook of your app). 

Afterwards, run `./ngrok http 5000` in the directory your ngrok is located

And also `python3 app.py` in another terminal

Try messaging your bot "hi", it should respond back with the same thing. Now you know your program is working!

## Commands
`ask (question),(possible_answer1),(possible_answer2),...,(possible_answern)` -> The bot will send you an ID that will be used to view\enter responses
`vote question_id` -> The bot will send you a list of possible responses, please click one of them to cast your vote!
`view question_id` -> The bot will show you how many of each response it received for the question

## Future Plans
- Generate random question_ids, similar to straw..errr surveymonkey
- `lynch question_id` -> Allow you to get the names of people/fb_id who voted for each response (as json maybe?)
- `spam_enemies question_id` -> Allow you to send a message of your choice to people who answered a certain response for question_id
- `anon xyz vote question_id` similar to `vote`, but your facebook id will be set to xyz. So `lynch` and `spam_enemies` commands will not work on you :) 

