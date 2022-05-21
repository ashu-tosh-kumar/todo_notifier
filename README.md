# TODO Notifier [WIP]

More often than not, we developers put some TODO item in code and forget about it. Sometimes, we think of coming back to a TODO item by some date but miss it being too busy with some other development.

TODO Notifier aims to solve this problem. It expects users to write TODO items in following format:

`TODO {2022-05-22} user_name msg`.

Above format has following components

- `TODO` is capital. It need not to be starting word of the comment
- TODO is followed a date in `YYYY-MM-DD` format within curly brackets. Respective TODO item is expected to be completed by end of this date
- Date is followed by a unqiue user name
- User name is followed by the usual message/comment of the respective TODO item

The code is robust in the sense that if the TODO item misses some data, the same will still be picked up by the TODO Notifier. However without relevant information, certain functionalities may not work. For e.g. without date, we cannot know if the TODO item has overshoot its expected date of completion.

TODO Notifier reads through all the files in a project, collect all the TODO items and send automated notifications (by default via Emails) to respective users and a group as a whole.

Other Salient Features:

- Allows excluding specific folders of the project via absolute address, relative address or regular expression from being scanned
- Allows excluding specific files of the project via absolute address, relative address or regular expression from being scanned
- Provides two default summaries produced
  - User wise list of TODO items expired already and to be expired in next week
  - Module wise list of all TODO items
- More summaries can be added easily by inheriting from `BaseSummaryGenerator` and adding the same to `config`
- Provides default implementation of sending notifications via Email
- More ways of notifications can be added easily by inheriting from `BaseNotifier`
