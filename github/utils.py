from __future__ import unicode_literals

__author__ = 'David Baum'

import os
import fcntl
import sys
import logging
import socket
import urllib
import traceback
import subprocess
from time import sleep
from contextlib import closing

from django.conf import settings

from git import (
    GitCommandError,
    InvalidGitRepositoryError,
    Repo, FetchInfo)
from git.util import rmtree, IterableList
from pygit2 import RemoteCallbacks, GitError, UserPass, KeypairFromMemory, clone_repository
from uritools import urisplit


class PyGit2Callbacks(RemoteCallbacks):
    def __init__(self, project, credentials=None, certificate=None):
        """
        Class for pygit2 remote callbacks.

        :return:
        """
        self.project = project
        self.processed_percentage = -1
        # 'x-oauth-basic' password is used only for projects imported from Github
        self.github_password = 'x-oauth-basic'
        # When the credentials are wrong libgit2 asks credentials infinitely. Let's prevent it by this flag
        self.was_asked_for_credentials = False

        super(PyGit2Callbacks, self).__init__(credentials, certificate)

    def transfer_progress(self, stats):
        processed = stats.received_objects
        total = stats.total_objects
        line = 'Cloning repo. Receiving objects: {0}/{1}'.format(processed, total)
        logging.info(line)
        if processed == total and stats.total_deltas:
            processed = stats.indexed_deltas
            total = stats.total_deltas
            line = 'Cloning repo. Resolving deltas: {0}/{1}'.format(processed, total)
            logging.info(line)
        new_percentage = int(100 * (float(processed) / float(total)))
        if self.processed_percentage != new_percentage:
            self.processed_percentage = new_percentage

    def credentials(self, url, username_from_url, allowed_types):
        url_parts = urisplit(url)
        scheme = url_parts.getscheme(default='ssh')

        if self.was_asked_for_credentials:
            logging.error('The credentials are invalid. '
                          'Finishing cloning as we get inifite loop while fetching the credentials for {}'.format(url))
            raise GitError('Inifite loop while fetching credentials. '
                           'This is a bug of libgit2 when credentials are invalid')

        logging.error('Asking for credentials for {}'.format(url))
        self.was_asked_for_credentials = True

        # For SSH we may use only our or user's private SSH keys, otherwise GitError is raised
        if scheme == 'ssh':
            if self.project.ssh_key:
                credentials = self._get_user_private_ssh_key_credentials()
        else:
            credentials = self._get_user_password_credentials()

        return credentials

    def _get_user_password_credentials(self):
        """Get a user-password pair that the user inputed during project adding"""
        return UserPass(self.project.git_username, self.project.git_password)

    def _get_user_private_ssh_key_credentials(self):
        """Get user's Private SSH Key credentials for a project that was added with that project."""
        return KeypairFromMemory(self.project.git_username, self.project.ssh_pubkey, self.project.ssh_key,
                                 self.project.ssh_key_passphrase)


class RepoTools(object):
    def __init__(self, project):
        self.project = project
        self.repo = None
        url_parts = urisplit(self.project.url)
        self.local_dir = f'{settings.GIT_REPOS_DIR}{url_parts.path}'
        self.local_dir = os.path.abspath(self.local_dir)

    def get_repo_url(self, new_scheme=None, new_username=None):
        """
        Construct the URL for the GIT repo.

        :param new_scheme:
            new scheme if we want to change URL scheme e.g. https <-> ssh

        :param new_username:
            new username if we want to change URL username. False - remove username from URL (except SSH)

        :return:
            the URL for the GIT repo
        """
        if not self.project:
            return ''

        url_parts = urisplit(self.project.url)
        scheme = new_scheme if new_scheme else url_parts.scheme
        git_username = new_username if new_username else self.project.git_username
        if new_username is False and scheme != 'ssh':
            git_username = ''
        port = url_parts.port or ''
        if port:
            port = ''.join([':', port])

        if scheme == 'ssh':
            url = ''.join([scheme, '://', urllib.quote_plus(git_username), '@', url_parts.host, port,
                           url_parts.path or '', url_parts.query or ''])
            return url

        url = ''.join([scheme, '://', url_parts.host, port, url_parts.path or '', url_parts.query or ''])

        # if we changed username, so it's 100% is not oauth2 access token
        if new_username is not None:
            return url

        # For https and git protocols, try to refresh oauth2 access token if any exists
        try:
            pygit2_callbacks = PyGit2Callbacks(self.project)
            pygit2_callbacks.credentials(url, git_username, None)
        except Exception:
            error = "\n".join(traceback.format_exc().splitlines())
            logging.error("Error occurred while fetching repo url {0}: {1}.".format(
                url,
                error
            ))

        return url

    def get_repo(self):
        """
        Return the local repo object.

        :param project:
            the git.Repo object

        :return:
            None
        """
        if os.path.exists(self.local_dir):
            try:
                self.repo = Repo(self.local_dir)
                return self.repo
            except InvalidGitRepositoryError:
                error = "\n".join(traceback.format_exc().splitlines())
                logging.error("Error occurred while fetching origin into the local dir {0}: {1}.".format(
                    self.local_dir,
                    error
                ))
        return None

    def delete_repo(self):
        """
        Remove the local repo dir.

        :return:
        """
        if os.path.exists(self.local_dir):
            logging.info("Removing the local repo {0}".format(self.local_dir))

            rmtree(self.local_dir)

    def update_repo(self):
        """
        Remove the local repo dir.

        :return:
        """
        if os.path.exists(self.local_dir):
            logging.info("Removing the local repo {0}".format(self.local_dir))

            rmtree(self.local_dir)

    def git_fetch(self):
        git_repo_url = self.get_repo_url()
        if os.path.exists(self.local_dir):
            logging.info(f"Fetching the new commits for {self.local_dir}")
            self.repo = Repo(self.local_dir)
            try:
                origin = self.repo.remotes.origin
                response: IterableList[FetchInfo] = origin.pull()
                for fetch_info in response:
                    if fetch_info.commit:
                        self.project.last_commit = fetch_info.commit
            except GitCommandError as e:
                error = f"Error occurred while cloning the repo with url {git_repo_url} to {self.local_dir}: {e}. "
                logging.error("Error occurred while cloning the repo with url {0} to {1}: {2}. "
                              "Finishing the task".format(git_repo_url, self.local_dir, e))
                self.project.last_error = error
            if self.project.pk:
                self.project.save()

    def pygit2_clone_repo(self):
        """
        Clone the repo by pygit2 for the project and returns repo object.

        pygit2 library has better progress interface than git library.

        :return: git.Repo object if cloned, otherwise None
        """
        git_repo_url = self.get_repo_url()
        if os.path.exists(self.local_dir):
            self.git_fetch()
        else:
            try:
                self.delete_repo()
                if self.project:
                    logging.error("Cloning {0} into {1}".format(git_repo_url, self.local_dir))
                    pygit2_callbacks = PyGit2Callbacks(self.project)
                    clone_repository(git_repo_url, self.local_dir, callbacks=pygit2_callbacks)
                    logging.error('Finished cloning {0} into {1}'.format(git_repo_url, self.local_dir))
                    if os.path.exists(self.local_dir):
                        self.repo = Repo(self.local_dir)

                        try:
                            origin = self.repo.remotes.origin
                            response: IterableList[FetchInfo] = origin.pull()
                            for fetch_info in response:
                                if fetch_info.commit:
                                    self.project.last_commit = fetch_info.commit
                        except GitCommandError as e:
                            error = f"Error occurred while cloning the repo with url {git_repo_url} to {self.local_dir}: {e}. "
                            logging.error("Error occurred while cloning the repo with url {0} to {1}: {2}. "
                                          "Finishing the task".format(git_repo_url, self.local_dir, e))
                            self.project.last_error = error
                            if self.project.pk:
                                self.project.save()
                elif self.local_dir:
                    self.repo = Repo(self.local_dir)
            except Exception:
                error = "\n".join(traceback.format_exc().splitlines())
                logging.error("Error occurred while cloning the repo with url {0} to {1}: {2}. "
                              "Finishing the task".format(git_repo_url, self.local_dir, error))
                self.project.last_error = error
                if self.project.pk:
                    self.project.save()
        return self.repo

    def clone_repo(self, silent=False):
        """
        Clone the repo for the project and returns repo object.

        :TODO: remove the method or adapt the command to accept SSH keys

        :return: git.Repo object if cloned, otherwise None
        """
        git_repo_url = self.get_repo_url()

        try:
            self.delete_repo()

            if self.project:
                logging.error("Cloning {0} into {1}".format(git_repo_url, self.local_dir))

                command = ["git", "clone", "--progress", git_repo_url, self.local_dir]
                fnull = open(os.devnull, 'w') if silent else None
                stdout = fnull if silent else subprocess.PIPE
                stderr = fnull if silent else subprocess.STDOUT
                git_clone_process = subprocess.Popen(
                    command,
                    bufsize=64,
                    stderr=stderr,
                    stdout=stdout
                )

                if not silent:
                    stdout = git_clone_process.stdout

                    fl = fcntl.fcntl(stdout, fcntl.F_GETFL)
                    fcntl.fcntl(stdout, fcntl.F_SETFL, fl | os.O_NONBLOCK)
                    while True:
                        try:
                            line = os.read(stdout.fileno(), 256)
                            if not line:
                                break
                            sys.stdout.write(line)

                            if self.project.task_id and line and line.strip():
                                meta = dict(description=line,
                                            processed_commits_number=0,
                                            project_id=self.project.pk,
                                            is_processing=True)
                                logging.info(f'Cloned project {self.project.name}: {meta}')
                        except OSError:
                            # waiting for data be available on fd
                            pass

                sout, serr = git_clone_process.communicate()

                if os.path.exists(self.local_dir):
                    self.repo = Repo(self.local_dir)
            elif self.local_dir:
                self.repo = Repo(self.local_dir)
        except GitCommandError:
            error = "\n".join(traceback.format_exc().splitlines())
            logging.error("Error occurred while cloning the repo with url {0} to {1}: {2}. finishing the task".format(
                git_repo_url, self.local_dir, error))
            self.project.last_error = error
            self.project.save()
        return self.repo


class AIApplicationRunner(object):
    LOGS_DIR = "logs"
    ACCESS_LOG = f"{LOGS_DIR}/access.log"
    ERROR_LOG = f"{LOGS_DIR}/error.log"
    ENV_DIR = ".env"

    def __init__(self, project):
        self.project = project

        self.url_parts = urisplit(self.project.url)
        self.local_dir = f'{settings.GIT_REPOS_DIR}{self.url_parts.path}'
        self.local_dir = os.path.abspath(self.local_dir)
        if not os.path.exists(self.local_dir):
            error_message = f'The project does not exist in {self.local_dir}'
            logging.info(error_message)

            repo_tools = RepoTools(project=project)
            repo_tools.pygit2_clone_repo()
        if not os.path.exists(f'{self.local_dir}/{self.LOGS_DIR}'):
            os.mkdir(f'{self.local_dir}/{self.LOGS_DIR}')
        dirname = os.path.dirname(self.local_dir)
        self.dirname = os.path.basename(dirname)

    def run(self):
        self.kill_application()

        if os.path.exists(self.env_path):
            rmtree(self.env_path)

        shell_command = ""
        if settings.CREATE_VIRTUAL_ENV:
            self.create_env()
            shell_command = f"""
                source {self.env_path}/bin/activate
            """

        shell_command = f"""
        {shell_command}
        pip install -r {self.local_dir}/requirements.txt
        cd {self.local_dir}
        printf 'from app import app' 'if __name__ == '__main__':' '    app.run()' > start.py
        gunicorn -b 0.0.0.0:{self.project.port} start:app --access-logfile {self.access_log_path} --error-logfile {self.error_log_path} --daemon
        """
        result = subprocess.run(
            shell_command,
            stdout=subprocess.PIPE,
            universal_newlines=True,
            shell=True
        )
        for line in result.stdout.split("\n"):
            logging.info(line)
        sleep(1)

    def create_env(self):
        if os.path.exists(self.local_dir):
            logging.info(f'Creating virtual env in {self.local_dir}')

            command = f"virtualenv -p python3 {self.env_path}"
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                universal_newlines=True,
                shell=True
            )
            for line in result.stdout.split("\n"):
                logging.info(line)

    def is_application_running(self):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(5)
            result = sock.connect_ex(("127.0.0.1", self.project.port))
            return result == 0

    def kill_application(self):
        is_running = self.is_application_running()
        if is_running:
            logging.info(f'Killing the application running on port {self.project.port}')
            pids = subprocess.run(
                ['lsof', '-t', f'-i:{self.project.port}'], text=True, capture_output=True
            ).stdout.strip()
            if pids:
                for pid in pids.split():
                    if subprocess.run(['kill', '-TERM', pid]).returncode != 0:
                        result = subprocess.run(['kill', '-KILL', pid], check=True)
                        logging.info(result)
                sleep(1)  # Give OS time to free up the PORT usage

        if os.path.exists(self.access_log_path):
            os.unlink(self.access_log_path)
        if os.path.exists(self.error_log_path):
            os.unlink(self.error_log_path)

    @property
    def env_path(self):
        return f"{self.local_dir}/{self.ENV_DIR}"

    @property
    def error_log_path(self):
        log_path = f"{self.local_dir}/{self.ERROR_LOG}"
        if not os.path.exists(log_path):
            try:
                open(log_path, 'a').close()
            except OSError:
                logging.error(f'Failed creating the {log_path}')
        return log_path

    @property
    def access_log_path(self):
        log_path = f"{self.local_dir}/{self.ACCESS_LOG}"
        if not os.path.exists(log_path):
            try:
                open(log_path, 'a').close()
            except OSError:
                logging.error(f'Failed creating the {log_path}')
        return log_path
