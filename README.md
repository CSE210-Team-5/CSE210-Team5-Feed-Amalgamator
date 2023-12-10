# Feed Amalgamator

This branch contains the initial version of the web application feed-amalgmator developed using Flask.

Please follow the instructions below to run the application:

1. Install Pycharm - <https://www.jetbrains.com/pycharm/download/?section=windows>. You can install any IDE that you like. But it is recommended to use Pycharm to keep the development environment clean.

2. Install python 3.11.5 - <https://www.python.org/downloads/release/python-3115/>

3. Install pdm - `pip install pdm`

4. Navigate to the project directory and run `pdm init`. This will automatically detect all python versions installed in your system and ask you to choose one. Choose python 3.11.5. When asked if you would like to create a new virtual environment choose "Yes". This will create a virtual environment specific to the project. You can ignore the other questions asked and skip them by pressing "Enter".

5. Run `pdm install`. This will resolve all dependency conflicts and install the required packages inside the projects folder and create a `pdm.lock` file.

6. Now when you open the project using pycharm it would automatically detect the virtual environment present inside the project folder and will choose that as the default interpreter.

7. Restart the terminal inside Pycharm.

8. Put the client.ini file in instance directory.

9. Run `flask --app feed_amalgamator run --debug` . This opens the site in your browser. In debug mode, you can make live changes in the code which will be reflected on the site without having to restart the server.

## Using Makefiles to use Linters and run Tests locally

1. Use `npm install` to install stylelint and ESLint.
2. Use `npm init @eslint/config` to get config file for ESLint.
3. Add Configuration Files for Testing in configuration directory.
4. Use following commands to run linter, test and test-coverage respectively,

`make lint`  
`make test`  
`make test-coverage`
