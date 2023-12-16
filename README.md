# Feed Amalgamator

[![Lint](https://github.com/CSE210-Team-5/CSE210-Team5-Feed-Amalgamator/actions/workflows/lint.yml/badge.svg)](https://github.com/CSE210-Team-5/CSE210-Team5-Feed-Amalgamator/actions/workflows/lint.yml)
[![python-tests](https://github.com/CSE210-Team-5/CSE210-Team5-Feed-Amalgamator/actions/workflows/python-tests.yml/badge.svg)](https://github.com/CSE210-Team-5/CSE210-Team5-Feed-Amalgamator/actions/workflows/python-tests.yml)
[![Static-Code-Analysis](https://github.com/CSE210-Team-5/CSE210-Team5-Feed-Amalgamator/actions/workflows/static-analysis.yml/badge.svg)](https://github.com/CSE210-Team-5/CSE210-Team5-Feed-Amalgamator/actions/workflows/static-analysis.yml)
[![Deploy static content to Pages](https://github.com/CSE210-Team-5/CSE210-Team5-Feed-Amalgamator/actions/workflows/Documentation_Generator.yml/badge.svg)](https://github.com/CSE210-Team-5/CSE210-Team5-Feed-Amalgamator/actions/workflows/Documentation_Generator.yml)
[![Build and Deploy](https://github.com/CSE210-Team-5/CSE210-Team5-Feed-Amalgamator/actions/workflows/Deployment_Workflow.yml/badge.svg)](https://github.com/CSE210-Team-5/CSE210-Team5-Feed-Amalgamator/actions/workflows/Deployment_Workflow.yml)

## Table of Contents

- [What is Feed Amalgamator](README.md#what-is-feed-amalgamator)
- [How to use it](README.md#how-do-i-use-it)
- [Instructions for Setting up Local Environment](README.md#instructions-for-setting-up-local-environment)
- [Using Makefiles to use Linters and run Tests locally](README.md#using-makefiles-to-use-linters-and-run-tests-locally)
- [Useful Links](README.md#useful-links)
- [The Team](README.md#what-is-feed-amalgamator)

## What is Feed Amalgamator?

Feed Amalgamator is a revolutionary platform designed to simplify and enhance your Mastodon usage. If you're tired of juggling multiple accounts across different Mastodon server instances, look no further. Our application empowers users to link various Mastodon accounts seamlessly, creating a unified feed for a more streamlined and enjoyable social media experience.

You can access our site here: <https://feedamalgamator.azurewebsites.net/>

## How do I use it?

- **Register An Account:**
  Getting started with Feed Amalgamator is quick and easy. Begin by registering an account using your preferred username and password. Head to our Registration
  Page to create your account and unlock the full potential of a unified Mastodon feed.
  
- **Add Mastodon Server Instances:**
  In your account settings, locate the "Add Server" option. Here, you can link various Mastodon server instances to amalgamate your feeds. Enter the server
  instance details, such as mastodon.social or mastodon.world, and follow the on-screen instructions.

- **OAuth Procedure:**
  For each Mastodon server instance you add, you'll need to complete the OAuth procedure. This is a secure authentication process that establishes a connection
  between Feed Amalgamator and your Mastodon accounts. Don't worry; we've streamlined the process to make it as seamless as possible.
  
- **Home Page: Your Amalgamated Feed:**
  Once you've added and authenticated your Mastodon server instances, head to the Feed Amalgamator homepage. Here, you'll find your newly created amalgamated feed,
  a single, centralized stream that combines all your Mastodon accounts.

You can also find the instructions for using the site here: <https://feedamalgamator.azurewebsites.net/about>

## Instructions for Setting up Local Environment

Please follow the instructions below to run the application:

1. Install Pycharm - <https://www.jetbrains.com/pycharm/download/?section=windows>. You can install any IDE that you like. But it is recommended to use Pycharm to keep the development environment clean.

2. Install python 3.11.5 - <https://www.python.org/downloads/release/python-3115/>

3. Install pdm - `pip install pdm`

4. Navigate to the project directory and run `pdm init`. This will automatically detect all python versions installed in your system and ask you to choose one. Choose python 3.11.5. When asked if you would like to create a new virtual environment choose "Yes". This will create a virtual environment specific to the project. You can ignore the other questions asked and skip them by pressing "Enter".

5. Run `pdm install`. This will resolve all dependency conflicts and install the required packages inside the projects folder and create a `pdm.lock` file.

6. Now when you open the project using pycharm it would automatically detect the virtual environment present inside the project folder and will choose that as the default interpreter.

7. Restart the terminal inside Pycharm.

8. Make a new directory named configuration and store app_settings.ini and test_mastodon_client_info.ini files in it. Request the team for these configuration files.

9. Run `flask --app feed_amalgamator run --debug` . This opens the site in your browser. In debug mode, you can make live changes in the code which will be reflected on the site without having to restart the server.

### Run Using Docker

1. Build the Docker Image: docker build . -t test
2. Run the container: docker run --publish 5000:80 test

### Using Makefiles to use Linters and run Tests locally

1. Use `npm install` to install stylelint and ESLint.
2. Use `npm init @eslint/config` to get config file for ESLint.
3. Add Configuration Files for Testing in configuration directory.
4. Use following commands to run linter, test and test-coverage respectively,

`make lint`  
`make test`  
`make test-coverage`

## Useful Links

- **Website:** <https://feedamalgamator.azurewebsites.net/>

- **Documentation:** <https://cse210-team-5.github.io/CSE210-Team5-Feed-Amalgamator/>

- **Architecture / Concept Diagrams:** <https://github.com/CSE210-Team-5/CSE210-Team5-Feed-Amalgamator/tree/Readme-Update-Revision-I/specs/Diagrams>

- **ADR:** <https://github.com/CSE210-Team-5/CSE210-Team5-Feed-Amalgamator/blob/305774855dfd771ef0410ac7b6c710b6a93922cd/specs/ADR.pdf>

- **Retrospective and Future Enhancements:** <https://github.com/CSE210-Team-5/CSE210-Team5-Feed-Amalgamator/blob/305774855dfd771ef0410ac7b6c710b6a93922cd/specs/Known_Issues_and_Future_Enhancements.pdf>

- **Process Documentation:** <https://github.com/CSE210-Team-5/CSE210-Team5-Feed-Amalgamator/blob/305774855dfd771ef0410ac7b6c710b6a93922cd/specs/Process.pdf>

- **Slide Decks:** <https://github.com/CSE210-Team-5/CSE210-Team5-Feed-Amalgamator/tree/Readme-Update-Revision-I/specs/>

- **Youtube Link (Launch): https://youtu.be/hMvNHG9saj4**
- 
## The Team Behind Feed Amalgamator

- [Brandon Wu](https://github.com/bwu2018)
- [Julian Rahimi](https://github.com/ju-ra-96)
- [Samarth Bhadane](https://github.com/samarth9201)
- [Shibani Likhite](https://github.com/ShibaniL123)
- [Srinivas](https://github.com/srinivasraman18)
- [Vancheeswaran Vaidyanathan](https://github.com/vancheeswaran)
- [Weijie CHIA](https://github.com/Moomootank)
