from bbc_stats import GithubSiteBase


class GithubData(GithubSiteBase):
    output_path = "_data"
    output_format = "json"
    output_kwargs = {"indent": 4}

    def parse(self, project_root_dir):
        pass
