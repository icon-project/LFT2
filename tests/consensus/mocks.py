from lft.consensus.round import Round


class RoundMock(Round):
    def __init__(self,):
        super(self).__init__(round_layer, node_id, epoch, round_num, event_system, data_factory, vote_factory)