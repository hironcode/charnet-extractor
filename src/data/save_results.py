

def save_plot_sentiment(path, title, data: dict[dict[str, float]]) -> None:
    """
    Save a plot of sentiment analysis as a csv file
    :param path: path to save the result
    :param title: title of the story. The file name will be the same as the title
    :param data: data of polarity to save
    :return: None
    """
    import pandas as pd

    df = pd.DataFrame(
        index=data.keys(),
        data=data.values()
    )
    df.columns = ['negative', 'neutral', 'positive', 'compound']
    df.to_csv(path + f"/{title}.csv")


def save_characters(path, title, data: dict[dict[str, float]]) -> None:
    """
    Save a plot of sentiment analysis as a csv file
    :param path: path to save the result
    :param title: title of the story. The file name will be the same as the title
    :param data: data of polarity to save
    :return: None
    """
    import pandas as pd

    df = pd.DataFrame(
        index=data.keys(),
        data=data.values()
    )
    df.columns = ['negative', 'neutral', 'positive', 'compound']
    df.to_csv(path + f"/{title}.csv")