# TypeTrace

This is the GitHub repository of the TypeTrace source code

## Installing the Project

You can install TypeTrace on any linux distro by pasting the following command into the terminal:

```
curl --proto '=https' --tlsv1.2 -sSf https://raw.githubusercontent.com/domi413/TypeTrace/main/install.sh | bash
```

Note that:

- The local install requires GTK4 to be installed.
- Flatpak simply requires flatpak to be installed.

## Running the Project

To test the project use the command `make test`, refer to the Makefile for further options.

## Spellchecking errors

If the Spellchecker throws an error, but the misspelled word should be accepted, add it to the corresponding dictionary. You can find the dictionaries under `.github/spellcheck/dictionaries/`.

## How to run Pipeline locally

To run the pipeline locally, we use the tool [act](https://github.com/nektos/act). After installing the tool, run `act` in the terminal. If you want to run a specific test, use `act -j [test]`.

### Setup GitHub Token

The act client needs a GitHub Token to work as intended.

1. Go to the [tokens](https://github.com/settings/tokens) page and create a new token.
2. Create the file `.secrets` in the root folder of the project.
3. Now add the following content to the file:

   ```
   GITHUB_TOKEN=your_token
   ACT=true
   ```

You should now be able to run the pipelines through the act client.
