import { info } from '@actions/core';
import { action, ActionInterface, Status } from './constants';
import { execute } from './utils';
import _once from 'lodash/once';
import { rmRF } from '@actions/io';

const init = _once(async (options: ActionInterface) => {
  info('Start check branch');

  try {
    await execute(
      `git config --global --add safe.directory "${options.workspace}"`,
      options.workspace
    );
  } catch {
    info('Unable to set workspace as a safe directory…');
  }

  await execute(`git config user.name "filestorage-action"`, options.workspace);

  await execute(
    `git config user.email "filestorage-action@@users.noreply.github.com"`,
    options.workspace
  );

  await execute(`git config core.ignorecase false`, options.workspace);
});

export async function checkTargetBranchExist(options: ActionInterface) {
  const output = (await execute('git branch -r', options.workspace)).stdout;
  const branchs = output.split('\n').map((s) => s.trim());

  return branchs.includes(`origin/${options.branch}`);
}

const temporaryStorageDirectory = '.branch-filestorage-action-temp';

/**
 * check storage branch exist
 */
export async function checkout(options: ActionInterface) {
  init(options);

  // TODO
}

/**
 * Save file into worktree
 */
export async function save(options: ActionInterface): Promise<Status> {
  init(options);

  const branchExists = await checkTargetBranchExist(options);

  await generateWorktree(options, branchExists);

  await execute(
    `cp -f ${options.path} ${options.workspace}/${temporaryStorageDirectory}`,
    options.workspace
  );

  if (options.singleCommit) {
    await execute(
      `git add --all .`,
      `${options.workspace}/${temporaryStorageDirectory}`
    );
  }

  // Use git status to check if we have something to commit.
  // Special case is singleCommit with existing history, when
  // we're really interested if the diff against the upstream branch
  // changed.
  const checkGitStatus =
    branchExists && options.singleCommit
      ? `git diff origin/${options.branch}`
      : `git status --porcelain`;

  info(`Checking if there are files to commit…`);

  const hasFilesToCommit = Boolean(
    (
      await execute(
        checkGitStatus,
        `${options.workspace}/${temporaryStorageDirectory}`,
        true // This output is always silenced due to the large output it creates.
      )
    ).stdout
  );

  if (!options.singleCommit && !hasFilesToCommit) {
    // No file changed
    return Status.SKIPPED;
  }

  // Commits to GitHub.
  await execute(
    `git add --all .`,
    `${options.workspace}/${temporaryStorageDirectory}`
  );

  await execute(
    `git commit -m "update filestorage at ${new Date().toISOString()}" --quiet --no-verify`,
    `${options.workspace}/${temporaryStorageDirectory}`
  );

  info(`Force-pushing changes...`);
  await execute(
    `git push --force origin ${options.branch}`,
    `${options.workspace}/${temporaryStorageDirectory}`
  );

  info(`Changes committed to the ${options.branch} branch… 📦`);

  return Status.SUCCESS;
}

/**
 * clean jobs
 */
export async function cleanupJobs(options: ActionInterface) {
  await execute(`chmod -R +rw ${temporaryStorageDirectory}`, options.workspace);

  await execute(
    `git worktree remove ${temporaryStorageDirectory} --force`,
    options.workspace
  );

  await execute(`git branch -D ${options.branch}`, options.workspace);

  await rmRF(temporaryStorageDirectory);
}

/**
 * generate worktree
 */
async function generateWorktree(
  options: ActionInterface,
  branchExists: boolean
) {
  info('Creating worktree…');

  if (branchExists) {
    await execute(
      `git fetch --no-recurse-submodules --depth=1 origin ${options.branch}`,
      options.workspace
    );
  }

  await execute(
    `git worktree add --no-checkout --detach ${temporaryStorageDirectory}`,
    options.workspace
  );

  const checkout = new GitCheckout(options.branch);

  if (branchExists) {
    // There's existing data on the branch to check out
    checkout.commitish = `origin/${options.branch}`;
  }

  if (
    !branchExists ||
    (options.singleCommit && options.branch !== process.env.GITHUB_REF_NAME)
  ) {
    /* Create a new history if we don't have the branch, or if we want to reset it.
      If the ref name is the same as the branch name, do not attempt to create an orphan of it. */
    checkout.orphan = true;
  }

  await execute(
    checkout.toString(),
    `${options.workspace}/${temporaryStorageDirectory}`
  );

  if (!branchExists) {
    info(`Created the ${options.branch} branch… 🔧`);

    // Our index is in HEAD state, reset
    await execute(
      'git reset --hard',
      `${options.workspace}/${temporaryStorageDirectory}`
    );

    if (!options.singleCommit) {
      // New history isn't singleCommit, create empty initial commit
      await execute(
        `git commit --no-verify --allow-empty -m "Initial ${options.branch} commit"`,
        `${options.workspace}/${temporaryStorageDirectory}`
      );
    }
  }
}

class GitCheckout {
  orphan = false;
  commitish?: string | null = null;
  branch: string;
  constructor(branch: string) {
    this.branch = branch;
  }
  toString(): string {
    return [
      'git',
      'checkout',
      this.orphan ? '--orphan' : '-B',
      this.branch,
      this.commitish || '',
    ].join(' ');
  }
}
