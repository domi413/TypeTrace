# TypeTrace
This is the GitHub repository of the TypeTrace source code

## Setup
All you need to do is run the `setup.sh` script on your machine. If you're running on Windows you can use WSL to execute it or the git bash.

## Local Pipeline Run

To run the pipeline locally, we use the tool [act](https://github.com/nektos/act). You can install the tool and then run `act` in a terminal.

## Spellcheck

If Spellcheck throws an error, but the word it doesn't accept is a word that should be accepted, add it to the corresponding dictionary. You can find the dictionaries in `.github/spellcheck/dictionaries`. If you have a Python codeword, add it to the `python.txt` file in a new line. For other words, please use the `project-words.txt` file and write it in the correct section. If you believe that we need a whole new dictionary, just ask for it.

### Setup GitHub Token

The act client needs a GitHub Token to work as intended.

1. Go to the [tokens](https://github.com/settings/tokens) page and create a new token.
2. Create the file `.secrets` in the root folder of the project.
3. Now add this content to the file: `GITHUB_TOKEN=your_token`
4. You also need to add this line to your file: `ACT=true`

After those steps you should be able to run the pipelines through the act client.