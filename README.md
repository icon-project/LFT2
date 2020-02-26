# LFT2
![Unittest](https://github.com/icon-project/LFT2/workflows/Unittest/badge.svg?branch=master)
![IntegrationTest](https://github.com/icon-project/LFT2/workflows/IntegrationTest/badge.svg?branch=master)

LFT2 is a new consensus algorithm inspired by PBFT. It improves TPS with reducing a pair of votes compared to PBFT when nodes make a consensus. A concept, 'Candidate' has been introduced for keeping safety.

This is implemented as a library. So not only blockchain but also any application which requires a byzantine fault tolerance consensus algorithm can integrate it.

This contains an example application for easy understanding. You can run it without integration. Also it composes multiple nodes in this single app. You can simulate byzantine node actions and observe how it tolerates the actions.

The paper of LFT2 will be released soon.


## Example Application
You can run example app using this command.

```shell
$ lft
```
This command runs 4 nodes. They make data as results of consensus. If you want to run it with 10 nodes then run this command below.

```shell
$ lft -n 10
```

You can see a lot of event logs.

```shell
16:18:34,085 0xd32b RoundEndEvent(is_success=True,epoch_num=1,round_num=1,candidate_id=0xd4ad,commit_id=0x6765)
```
Event log consists of time, node id and event. This log means round 1 ends successfully with deciding a new candidate. Each round makes a consensus to determine one candidate. A candidate is committed after when next new candidate connected to the candidate is decided. In this case `0xd4ad` is connected to `0x6765`. `0x6765` has already been decided in previous round.

#### Replay
```shell
$ lft record
```
It records event logs for replaying. The log path is `./data`. It contains all nodes' events.

```shell
$ lft replay -t 1abde1d6c2eb942df4686116d64f889d
```
The argument `1abde1d6c2eb942df4686116d64f889d` is one of nodes' id located in log path after running with recording command.

## Integration
Some components are provided for integration. Applications which want to use LFT have to customize abstract classes.

```
Data(Block), DataFactory(BlockFactory), Vote, VoteFactory, Epoch
```

The applications have to post the event.

```
RoundStart
```

The applications must listen the events.
```
RoundEnd, BroadcastData, BroadcastVote, ReceiveData, ReceiveVote
```

Note that LFT2 is not responsible for node communication, storing blocks and executing transactions. So the applications must implement them.
