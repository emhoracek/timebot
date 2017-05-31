# TIMEBOT

This is a bot that reminds you to log hours, so your teammates don't have to!

## Setup

`/timebot add YOUR\_TOGGL\_KEY` will setup up your Toggl. You can get your API
token from [your Toggl profile](https://toggl.com/app/profile).

Next, go to the 
[Incoming Webhooks](https://positiondev.slack.com/apps/A0F7XDUAZ-incoming-webhooks) 
page in Position's Slack settings. Click the green "Add Configuration" 
button. Then, in the "Post to Channel" drop-down, select your own Direct Messages
channel. Copy the webhook URL.

`/timebot hook http://slack.com/yourwebhook` will set up your webhook for
reminders.

`/timebot remind 5pm` will set a reminder for 5pm daily. If you already had a
reminder set, your reminder will be changed to the new time. (You can't set a 
reminder for more than once a day.)

`/timebot vacation 3 days` will pause reminders for 3 days. (Useful for vacation.)

`/timebot bankrupt` will declare Toggl bankruptcy. Timebot will go back to only 
showing entries from the last 24 hours.

## Commands

Use `/timebot verify` to verify that your entries are up-to-date. Timebot will
show you all your entries since the last time you verified. Click "yes" to
confirm.

`/timebot entries` will show your entries from the last time you verified the
entries.

## Reminders

If you set up reminders, Timebot will message you every weekday at the time you
specified when you set it up.

Timebot will show you every entry logged since the last time you confirmed
your entires. If you've never confirmed any entries, then it'll show all the
entries since the day before you set up your Timebot.

After displaying entries, Timebot will ask, "Is this all the work you did since
(DATE)"? You can enter `/timebot yes` to confirm your entries, or enter
`/timebot no` (or do nothing) for more time.

`/timebot done` will let Timebot know you're finished adjusting your entries.
Timebot will show the entries again and ask for confirmation, just like
`/timebot verify`. (ED: because it's just an alias for `/timebot verify`)

## Entry listings

Timebot only lists the description and duration of each entry. Timebot will also
highlight long periods of time between entries and very short entries.

|------------------------|
| Description | Duration |
|------------------------|
| Some entry  | 1:30     |
| Some entry  | 0:05     |
|     **Long gap**       |
| Another     | 1:30     |
|------------------------|

## In-Slack help

`/timebot help` shows a list of all the commands.
