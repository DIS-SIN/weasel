## Weasel (Web Enabled AI Support Expression Learner)

Weasels are small yet very competent hunters. They can find things and retrieve things even in the most inaccessible of places. 

This app is kind of like one of those weasels... It's an app that helps you find things to help you learn stuff or do stuff. Weasel, the Web Enabled AI Support Expression Learner - helping you better understand a digital government (With Easy Available Smart E-Learning) lets you get the information that matters to you. There's a lot of great content and sites out there for us to improve and grow, but sometimes just gettign started is the hard part.

That's where Weasel comes in. 

You ask weasel things like **"why is digital important for goverment"**, **"why should TBS care about open source"**, Suggested Weasel Queries: **"why does open souce matter to me"**, **"access my service canada account"**, **"I want to become a citizen"**, **"why does digital matter to my department"**, **"I want to learn french"**, **"Renew my passport"**, **"what skills do I need for digital"** and weasel will find you online learning tools (and some guiding information to help you get rolling). We don't want to just give you a list, that doesn't help as much as people hope. We aim to give you knowledge, what you can do, how you'd learn, if there are any hints from the experts in the industry.

Our goal is to get you learning by clearing the weeds and critters in your path. That's what Weasel is for.

But it doesn't end there. With the right training the Weasel can play fetch, even help you renew your passport or checkout your benefits. 

The only limitations are how well we treat the Weasel.

### Tools and Technology

The experimental apps here are built on the following stack:

* Weasel is built with HTML, [SASS](http://sass-lang.com/), JS / [jQuery](https://jquery.com/), [Metro4](https://metroui.org.ua/index.html)
* As our ai framework we are using [wit.ai](http://wit.ai/), but aim to support multiple frameworks
* The data is all JSON files, we curated it from various assets across the web
* The server-side is an [Azure](https://azure.microsoft.com/en-ca/) cloud running an [Ubuntu VM](https://www.ubuntu.com/), [Python 3](https://www.python.org/downloads/release/python-370/), [Flask](http://flask.pocoo.org/), and [nginx](https://www.nginx.com/)
* We automate our deploys with crontab and [pm2](https://pm2.io/doc/)

> Note: Our long term aspiration goal here is to have you be able to naturally speak to weasel about work related stuff and it would actually be useful. You'd ask a question and the weasel would find you the best way to move forward. Our goal is to experiment with the AI platforms out there to see if we can make really compelling experiences for the humans. We also want to try and stay as AI system agnostic as possible, while still making the data we generate open and modular.

### Getting/Refreshing the Data

All the data is raw JSON, getting the data is as simple as loading the link. The data was generated manually by doing some legwork for the learner and building an easy to navigate hot list of content. 

There's also an api baked in which returns json answers. This can be used to embed weasel functionality into almost any endpoint

```bash
http://localhost:5050/weasel/api?weasel_ask=why+does+open+source+matter+to+government
```

> Note: The aspirational goal here is to have a crowd sourced feed in from people who find nice treats on the web or their own expert brains and feed it to the Weasel. As the answer knowledge increases, and we refine the understanding of the model... It could be truly great.

### Weasel answer JSON

The JSON is standard, but we use hints to help serve to best content in the best way. The answer intuition uses a direct match or a * match to determine applicability. Then the action (currently there are display and access) will trigger weasel to do what is needed.

* "display" is used for returning an html answer card with the details available to the user
* "access" will use the hyperlink and redirect the human to the appropriate link 

```json
{
	"intent": "access site",
	"topic_interest": "canada.ca",
	"impact_on": "*",
	"key_party": "*",
	"answer": {
		"type": "weasel-answer",
		"action": "access",
		"media": "2378528 visitors have accessed the link I found",
		"hyperlink": "https://www.canada.ca/en.html",
		"spoken": "Access Canada.ca Home page",
		"written": "Access Canada.ca Home page"
	}
},
```

### Building the Stylesheets

* Install [Sass](http://sass-lang.com/):
* If you are on windows without make, just directly use sass

```bash
cd wheremystufflives/development/weasel/
sass sass/weasel.css.scss:sass/weasel.css
```
This will create the css files you need. When your testing is done, move htem into the css directory

* Assuming you have make, to watch the Sass source for changes and build the stylesheets automatically, run:

```bash
make watch
```

* To compile the Sass stylesheets once, run:

```bash
make clean all
```

or:

```bash
# -B tells make to run even if the .css file exists
make -B
```

### Updating code and commit to repo

* Switch to dev branch, get changes

```bash
git checkout temp_branch
git pull
```

* Make your changes to templates/styles
* Rebuild stylesheets (see above)

```bash
cd wheremystufflives/development/weasel/
sass sass/weasel.css.scss:sass/weasel.css
```

* If your stylesheets look good, go ahead and copy them into the static/whatmyappiscalled/css/ of the app you're modifying. If you're feeling brave, you can just write out the files to the static directory from sass
* Test changes locally with anaconda in (base) by launching an ananconda terminal window

```bash
cd wheremystufflives/development/weasel/
python application.py
```

* The site should now serve on localhost:5050
* Make sure everything works as you expect, then send it into the repo

```bash
git add .
git commit -m "update msg"
git push
```

### Deploying the app

* Have your project lead merge the temp branch into master
* Deploy master branch code by logging into your cloud instance vm

```bash
 ssh myusername@mydomain.wherever
 cd ~
 sh update_app.sh
 logout
 ```

### Thanks and mentions

The entire team at CSPS both DIS and DAT - you are all an inspiration.

### Public domain

This project is in the worldwide [public domain](LICENSE.md). As stated in [CONTRIBUTING](CONTRIBUTING.md):

> This project is in the public domain within the Canada, and copyright and related rights in the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).
>
> All contributions to this project will be released under the CC0 dedication. By submitting a pull request, you are agreeing to comply with this waiver of copyright interest.
