import numpy as np
import wandb
import torch
import torch.utils.data
from torch import nn

import pytorch_lightning as pl
from networks.dfae import DeepFakesAutoEncoder
from torch.optim import Adam

class DeepFakesModel(pl.LightningModule):

    def __init__(self):
        super().__init__()
        self.dfae = DeepFakesAutoEncoder()

    def forward(self, src_img, dst_img):
        swapped = self.dfae(src_img, 'dst')
        return swapped

    def training_step(self, batch, batch_idx, optimizer_idx=0):
        src_img, dst_img = batch
        recons_src = self.dfae(src_img, 'src')
        recons_dst = self.dfae(dst_img, 'dst')
        src_loss = nn.MSELoss()(recons_src, src_img)
        dst_loss = nn.MSELoss()(recons_dst, dst_img)
        swapped = self.dfae(dst_img, 'src')
        loss = src_loss + dst_loss
        log_imgs = torch.cat([src_img, recons_src, dst_img, recons_dst, swapped], axis=0)
        if self.global_step % 50 == 0:
            self.logger.experiment.log({
                "loss": loss,
                "images" : wandb.Image(log_imgs)
            })
        return loss

    def configure_optimizers(self):
        optimizer_1 = Adam([
            {'params': self.dfae.encoder.parameters()},
            {'params': self.dfae.inter.parameters()},
            {'params': self.dfae.decoder_src.parameters()}], 
            lr=5e-5, betas=(0.5, 0.999))
        optimizer_2 = Adam([
            {'params': self.dfae.encoder.parameters()},
            {'params': self.dfae.inter.parameters()},
            {'params': self.dfae.decoder_dst.parameters()}],
            lr=5e-5, betas=(0.5, 0.999))
        return [optimizer_1, optimizer_2]
