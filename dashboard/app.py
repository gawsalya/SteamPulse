"""Python Script: Build a dashboard for data visualization"""
from datetime import datetime
from os import environ, _Environ

import altair as alt
from altair.vegalite.v5.api import Chart
from dotenv import load_dotenv
import pandas as pd
from pandas import DataFrame
import streamlit as st
from psycopg2 import connect
from psycopg2.extensions import connection


def get_db_connection(config_file: _Environ) -> connection:
    """
    Returns connection to the database

    Args:
        config (_Environ): A file containing sensitive values

    Returns:
        connection: A connection to a Postgres database
    """
    try:
        return connect(
            database=config_file["DB_NAME"],
            user=config_file["DB_USER"],
            password=config_file["DB_PASSWORD"],
            port=config_file["DB_PORT"],
            host=config_file["DB_HOST"]
        )
    except Exception as err:
        print("Error connecting to database.")
        raise err


def get_database(conn_postgres: connection) -> DataFrame:
    """
    Returns redshift database transaction table as a DataFrame Object

    Args:
        conn_postgres (connection): A connection to a Postgres database

    Returns:
        DataFrame:  A pandas DataFrame containing all relevant release data
    """
    query = f""
    df_releases = pd.read_sql_query(query, conn_postgres)

    return df_releases


def build_sidebar_title(df_releases: DataFrame) -> list:
    """
    Build sidebar with dropdown menu options

    Args:
        df_releases (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        list:  A list with game titles that the user selected
    """
    titles = st.sidebar.multiselect(
        "Release Title:", options=sorted(df_releases["title"].unique()))
    return titles


def build_sidebar_release_date(df_releases: DataFrame) -> list:
    """
    Build sidebar with dropdown menu options to select release dates

    Args:
        df_releases (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        list: A list with release dates that the user selected
    """
    release_dates = st.sidebar.multiselect(
        "Release Date:", options=df_releases["release_date"].dt.date.unique())
    return release_dates


def build_sidebar_review_date(df_releases: DataFrame) -> list:
    """
    Build sidebar with dropdown menu options to select review dates

    Args:
        df_releases (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        list: A list with review dates that the user selected
    """
    dates = st.sidebar.multiselect(
        "Review Date:", options=df_releases["review_date"].dt.date.unique())
    return dates


def build_sidebar_genre(df_releases: DataFrame) -> list:
    """
    Build sidebar with dropdown menu options to select game genre

    Args:
        df_releases (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        list: A list with game genres that the user selected
    """
    dates = st.sidebar.multiselect(
        "Genre:", options=df_releases["genre"].unique())
    return dates


def build_sidebar_platforms() -> list:
    """
    Build sidebar with platform selection options

    Returns:
        list: A list with selected platforms
    """
    platforms = ["mac", "windows", "linux"]
    selected_platforms = st.sidebar.multiselect(
        "Compatible Platforms:", options=platforms, default=platforms)
    return selected_platforms


def build_sidebar_sentiment(df_releases: DataFrame) -> tuple:
    """
    Build sidebar with slider option to select range for review sentiment

    Args:
        df_releases (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        list: A tuple with minimum and maximum sentiment that the user has selected
    """
    sentiment = st.sidebar.slider(
        "Sentiment:", min_value=0.0, max_value=5.0, value=(0.0, 5.0), step=0.1)
    return sentiment


def filter_data(df_releases: DataFrame, titles: list[str], release_dates: list[datetime], review_dates: list[datetime],
                genres: list[str], platforms: list[str], minimum_sentiment: float, maximum_sentiment: float) -> DataFrame:
    """
    Apply live filtering according to sidebar filters to the data frame

    Args:
        df_releases (DataFrame): A DataFrame containing all data related to new releases

        titles (list[str]):  A list with game titles that the user selected

        release_dates (list[datetime]): A list with release dates that the user selected

        review_dates (list[datetime]): A list with review dates that the user selected

        genres (list[str]): A list with game genres that the user selected

        platforms (list[str]): A list with selected platforms

    Returns:
        DataFrame: A DataFrame containing filtered data related to new releases

    """
    if titles:
        df_releases = df_releases[df_releases["title"].isin(titles)]
    if release_dates:
        df_releases = df_releases[df_releases["release_date"].dt.floor(
            "D").isin(release_dates)]
    if review_dates:
        df_releases = df_releases[df_releases["review_date"].dt.floor(
            "D").isin(review_dates)]
    if genres:
        df_releases = df_releases[df_releases["genre"].isin(genres)]

    df_releases = df_releases[df_releases[platforms].any(axis=1)]
    df_releases = df_releases[(df_releases['sentiment'] >= minimum_sentiment) &
                              (df_releases['sentiment'] <= maximum_sentiment)]

    return df_releases


def plot_games_release_frequency(df_releases: DataFrame) -> Chart:
    """
    Create a line chart for the number of games released per day

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        Chart: A chart displaying plotted data
    """
    df_releases = df_releases.groupby("release_date")[
        "title"].nunique().reset_index()
    df_releases.columns = ["release_date", "num_of_games"]
    custom_ticks = [i for i in range(
        0, df_releases["num_of_games"].max() + 1)]

    chart = alt.Chart(df_releases).mark_line(
        color="#44bd4f"
    ).encode(
        x=alt.X("release_date:O", title="Release Date",
                timeUnit="yearmonthdate"),
        y=alt.Y("num_of_games:Q", title="Number of Games",
                axis=alt.Axis(values=custom_ticks, tickMinStep=1, titlePadding=10))
    ).properties(
        title="New Releases per Day",
        width=800,
        height=400
    )

    return chart


def plot_games_review_frequency(df_releases: DataFrame) -> Chart:
    """
    Create a line chart for the number of games released per day

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        Chart: A chart displaying plotted data
    """
    df_releases = df_releases.groupby(
        "release_date").size().reset_index()
    df_releases.columns = ["release_date", "num_of_reviews"]
    custom_ticks = [i for i in range(
        0, df_releases["num_of_reviews"].max() + 1)]

    chart = alt.Chart(df_releases).mark_line(
        color="#44bd4f"
    ).encode(
        x=alt.X("release_date:O", title="Release Date",
                timeUnit="yearmonthdate"),
        y=alt.Y("num_of_reviews:Q", title="Number of Reviews", axis=alt.Axis(
            values=custom_ticks, tickMinStep=1, titlePadding=10)),
    ).properties(
        title="New Reviews per Day",
        width=800,
        height=400
    )

    return chart


def plot_reviews_per_game_frequency(df_releases: DataFrame) -> Chart:
    """
    Create a bar chart for the number of reviews per game

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        Chart: A chart displaying plotted data
    """
    df_releases = df_releases.groupby(
        "title").size().reset_index()
    df_releases.columns = ["title", "num_of_reviews"]
    custom_ticks = [i for i in range(
        0, df_releases["num_of_reviews"].max() + 1)]

    chart = alt.Chart(df_releases).mark_bar(
    ).encode(
        x=alt.X("num_of_reviews", title="Number of Reviews",
                axis=alt.Axis(values=custom_ticks, tickMinStep=1, titlePadding=10)),
        y=alt.Y("title", title="Release Title", sort="-x")
    ).properties(
        title="Number of Reviews per Release",
        width=800,
        height=400
    )

    return chart


def plot_platform_distribution(df_releases: DataFrame) -> Chart:
    """
    Create a bar chart for the platform compatibility of games

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        Chart: A chart displaying plotted data
    """
    try:
        mac_compatibility = df_releases.groupby("mac")['title'].nunique()[True]
    except KeyError:
        mac_compatibility = 0
    try:
        windows_compatibility = df_releases.groupby(
            "windows")['title'].nunique()[True]
    except KeyError:
        windows_compatibility = 0
    try:
        linux_compatibility = df_releases.groupby(
            "linux")['title'].nunique()[True]
    except KeyError:
        linux_compatibility = 0

    compatibility_df = pd.DataFrame({"platform": ['mac', 'windows', "linux"],
                                     "compatibility": [mac_compatibility, windows_compatibility, linux_compatibility]})

    custom_ticks = [i for i in range(
        0, compatibility_df["compatibility"].max() + 1)]

    chart = alt.Chart(compatibility_df).mark_bar().encode(
        x=alt.X("platform", title="Platform"),
        y=alt.Y("compatibility", title="Compatible Games",
                axis=alt.Axis(values=custom_ticks, tickMinStep=1, titlePadding=10)),
    ).properties(
        title="Releases Compatibility per Platform",
        width=800,
        height=400
    )

    return chart


def plot_genre_distribution(df_releases: DataFrame) -> Chart:
    """
    Create a line chart for the number of games released per day

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        Chart: A chart displaying plotted data
    """
    df_releases = df_releases.groupby(
        "genre").size().reset_index()
    df_releases.columns = ["genre", "releases_per_genres"]
    custom_ticks = [i for i in range(
        0, df_releases["releases_per_genres"].max() + 1)]

    chart = alt.Chart(df_releases).mark_bar().encode(
        x=alt.X("releases_per_genres", title="Number of Releases",
                axis=alt.Axis(values=custom_ticks, tickMinStep=1, titlePadding=10)),
        y=alt.Y("genre:N", title="Genre")
    ).properties(
        title="Releases per Genre",
        width=800,
        height=400
    )

    return chart


def dashboard_header() -> None:
    """
    Build header for dashboard to give it title text

    Args:
        None

    Returns:
        None
    """

    st.title("SteamPulse")
    st.markdown("Community Insights for New Releases on Steam")


def sidebar_header() -> None:
    """
    Add text to the dashboard side bar

    Args:
        None

    Returns:
        None
    """
    with st.sidebar:
        st.markdown("Filter Options\n---")


def headline_figures(df_releases: DataFrame) -> None:
    """
    Build headline for dashboard to present key figures for quick view of overall data

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        None
    """
    cols = st.columns(3)
    st.markdown(
        """
        <style>
            [data-testid="stMetricValue"] {
            font-size: 25px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    with cols[0]:
        st.metric("Total Releases:", df_releases["title"].nunique())
    with cols[1]:
        st.metric("Total Reviews:",
                  df_releases.shape[0])
    with cols[2]:
        st.metric("Average Sentiment:", df_releases["sentiment"].mean())


def sub_headline_figures(df_releases: DataFrame) -> None:
    """
    Build sub-headline for dashboard to present key figures for quick view of overall data

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        None
    """
    try:
        mac_compatibility = df_releases.groupby("mac")['title'].nunique()[True]
    except KeyError:
        mac_compatibility = 0
    try:
        windows_compatibility = df_releases.groupby(
            "windows")['title'].nunique()[True]
    except KeyError:
        windows_compatibility = 0
    try:
        linux_compatibility = df_releases.groupby(
            "linux")['title'].nunique()[True]
    except KeyError:
        linux_compatibility = 0

    compatibility_df = pd.DataFrame({"platform": ['mac', 'windows', "linux"],
                                     "compatibility": [mac_compatibility, windows_compatibility, linux_compatibility]})

    cols = st.columns(3)
    st.markdown(
        """
        <style>
            [data-testid="stMetricValue"] {
            font-size: 25px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    with cols[0]:
        st.metric("Most Released Genre:", df_releases["genre"].mode()[0])
    with cols[1]:
        st.metric("Most Reviewed Release:", df_releases["title"].mode()[0])
    with cols[2]:
        st.metric("Most Compatible Platform",
                  compatibility_df["platform"].max().capitalize())

    st.markdown("---")


def first_row_figures(platform_distribution_plot: Chart, release_frequency_plot: Chart, review_frequency_plot: Chart) -> None:
    """
    Build figures relating to release and review frequency for dashboard

    Args:
        release_frequency_plot (Chart): A chart displaying plotted data

        review_frequency_plot (Chart): A chart displaying plotted data

    Returns:
        None
    """
    cols = st.columns(3)
    with cols[0]:
        st.altair_chart(release_frequency_plot, use_container_width=True)
    with cols[1]:
        st.altair_chart(review_frequency_plot, use_container_width=True)
    with cols[2]:
        st.altair_chart(platform_distribution_plot, use_container_width=True)

    st.markdown("---")


def second_row_figures(genre_distribution_plot: Chart, reviews_per_game_frequency_plot: Chart) -> None:
    """
    Build figures relating to release and review frequency for dashboard

    Args:
        genre_distribution_plot (Chart): A chart displaying plotted data

        platform_distribution_plot (Chart): A chart displaying plotted data

    Returns:
        None
    """
    cols = st.columns(2)
    with cols[0]:
        st.altair_chart(genre_distribution_plot, use_container_width=True)
    with cols[1]:
        st.altair_chart(reviews_per_game_frequency_plot,
                        use_container_width=True)

    st.markdown("---")


if __name__ == "__main__":

    # Temporary mock data
    game_df = pd.read_csv("mock_data.csv")
    game_df["release_date"] = pd.to_datetime(
        game_df['release_date'], format='%d/%m/%Y')
    game_df["review_date"] = pd.to_datetime(
        game_df['review_date'], format='%d/%m/%Y')

    # Start of dashboard script
    load_dotenv()
    config = environ

    # conn = get_db_connection(config)

    # game_df = get_database(conn)

    st.set_page_config(layout="wide")

    dashboard_header()

    sidebar_header()

    selected_releases = build_sidebar_title(game_df)
    selected_release_dates = build_sidebar_release_date(game_df)
    selected_review_dates = build_sidebar_review_date(game_df)
    selected_genre = build_sidebar_genre(game_df)
    selected_platform = build_sidebar_platforms()
    min_sentiment, max_sentiment = build_sidebar_sentiment(game_df)

    filtered_df = filter_data(game_df, selected_releases, selected_release_dates, selected_review_dates,
                              selected_genre, selected_platform, min_sentiment, max_sentiment)

    headline_figures(filtered_df)

    sub_headline_figures(filtered_df)

    reviews_per_game_release_frequency_plot = plot_reviews_per_game_frequency(
        filtered_df)
    games_release_frequency_plot = plot_games_release_frequency(filtered_df)
    games_review_frequency_plot = plot_games_review_frequency(filtered_df)
    games_platform_distribution_plot = plot_platform_distribution(filtered_df)
    games_genre_distribution_plot = plot_genre_distribution(filtered_df)

    first_row_figures(games_platform_distribution_plot, games_release_frequency_plot,
                      games_review_frequency_plot)
    second_row_figures(
        games_genre_distribution_plot,  reviews_per_game_release_frequency_plot)