## Weasel (With Easy Available Smart E-Learning)

Weasels are small yet very competent hunters. They can find things and retrieve things even in the most inaccessible of places. 

This app is not one of those weasels... It's an app that helps you learn. Weasel (With Easy Available Smart E-Learning) lets you learn how to learn. There's a lot of great content and sites out there for us to improve and grow, but sometimes just gettign started is the hard part.

That's where Weasel comes in. You ask weasel "why is digital important for goverment", and weasel will find you online learning tools (and some guiding information to help you get rolling). We don't want to just give you a list, that doesn't help as much as people hope. We aim to give you knowledge, what you can do, how you'd learn, if there are any hints from the experts in the industry.

Our goal is to get you learning by clearing the weeds and critters in your path. That's what Weasel is for.

### Tools and Technology

The experimental apps here are built on the following stack:

* Weasel is built with HTML, [SASS](http://sass-lang.com/), JS / [jQuery](https://jquery.com/), [Metro4](https://metroui.org.ua/index.html)
* The data is all JSON files, we curated it from various assets across the web
* The server-side is an [Azure](https://azure.microsoft.com/en-ca/) cloud running an [Ubuntu VM](https://www.ubuntu.com/), [Python 3](https://www.python.org/downloads/release/python-370/), [Flask](http://flask.pocoo.org/), and [nginx](https://www.nginx.com/)
* We automate our deploys with crontab and [pm2](https://pm2.io/doc/)

> Note: Our long term aspiration goal here is to have you be able to physically speak to weasel. You'd ask a question and the weasel would find you the best way to move forward. Our goal is to experiment with the AI platforms out there to see if we can make really compelling experiences for the user. We also want to try and stay as AI system agnostic as possible, while still making the data we generate open and modular.

### Getting/Refreshing the Data

Since all the data is raw JSON, getting the data is as simple as loading the link. The data was generated manually by doing some legwork for the learner and building an easy to navigate hot list of content.


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

* The site should now serve on localhost:5000
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

Since the weasel is essentially just html/js/css at it's heart, you can drop the code on basically any webserver with minimal edits and be off to the races.

If you are developing locally, you can do what we did during our initial sprint and run a simple python http server. We started this entirely offline, and then made it into a Flask app when we got closer to an alpha version. In a shell run the following in your development directory where this code lives:

```bash
cd wheremystufflives/development/ # weasel folder is here
python -m http.server
```

You should then be able to view the dashboard on `localhost:8000/weasel/`

### Public domain

This project is in the worldwide [public domain](LICENSE.md). As stated in [CONTRIBUTING](CONTRIBUTING.md):

> This project is in the public domain within the Canada, and copyright and related rights in the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).
>
> All contributions to this project will be released under the CC0 dedication. By submitting a pull request, you are agreeing to comply with this waiver of copyright interest.
