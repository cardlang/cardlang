"""The prototype's native library (VM5): the non-cryptographic part of the catalog (HAL-3). Stage 2: a placeholder;
the APIs arrive in stage 3.
"""
import vm

class Natives:
    def __init__(self, hal):
        self.hal = hal

    def call(self, ctx, number):
        raise vm.Trap("VM")                      # stage 3

    def end_command(self, ctx):
        pass                                     # command-lifetime keys and operations end here (VEX-48), stage 3

    def drop_session(self, ctx):
        pass
