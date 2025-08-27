import { Router } from 'express';
import { z } from 'zod';
import { DealStage } from '@prisma/client';
import { prisma, io } from '../../server';
import { auth } from '../../middlewares/auth.middleware';
import { validate } from '../../middlewares/validate.middleware';
import { logger } from '../../utils/logger';

const router = Router();

const createDealSchema = z.object({
  title: z.string().min(1),
  companyId: z.string(),
  contactId: z.string().optional(),
  stage: z.enum(['NEW', 'QUALIFIED', 'PROPOSAL', 'NEGOTIATION', 'WON', 'LOST']).optional(),
  amount: z.number().optional(),
  currency: z.string().default('EUR'),
  probability: z.number().min(0).max(100).default(50),
  expectedClose: z.string().optional(),
  source: z.string().optional(),
  notes: z.string().optional(),
  tags: z.array(z.string()).optional(),
});

// Get all deals with filters
router.get('/', auth, async (req, res, next) => {
  try {
    const { stage, ownerId, companyId, search } = req.query;
    
    const where: any = {};

    if (stage) {
      where.stage = stage as DealStage;
    }

    if (ownerId) {
      where.ownerId = ownerId;
    } else if (req.user!.role === 'SALES_REP') {
      // Sales reps only see their own deals
      where.ownerId = req.user!.id;
    }

    if (companyId) {
      where.companyId = companyId;
    }

    if (search) {
      where.title = {
        contains: search as string,
        mode: 'insensitive',
      };
    }

    const deals = await prisma.deal.findMany({
      where,
      include: {
        company: {
          select: {
            id: true,
            name: true,
          },
        },
        contact: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
          },
        },
        owner: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
          },
        },
      },
      orderBy: { createdAt: 'desc' },
    });

    res.json({ deals });
  } catch (error) {
    next(error);
  }
});

// Get pipeline view (grouped by stage)
router.get('/pipeline', auth, async (req, res, next) => {
  try {
    const where: any = {};
    
    if (req.user!.role === 'SALES_REP') {
      where.ownerId = req.user!.id;
    }

    const deals = await prisma.deal.findMany({
      where,
      include: {
        company: {
          select: {
            id: true,
            name: true,
          },
        },
        contact: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
          },
        },
        owner: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
            avatar: true,
          },
        },
      },
      orderBy: { updatedAt: 'desc' },
    });

    // Group by stage
    const pipeline = {
      NEW: deals.filter(d => d.stage === 'NEW'),
      QUALIFIED: deals.filter(d => d.stage === 'QUALIFIED'),
      PROPOSAL: deals.filter(d => d.stage === 'PROPOSAL'),
      NEGOTIATION: deals.filter(d => d.stage === 'NEGOTIATION'),
      WON: deals.filter(d => d.stage === 'WON'),
      LOST: deals.filter(d => d.stage === 'LOST'),
    };

    // Calculate stage totals
    const totals = Object.entries(pipeline).reduce((acc, [stage, stageDeals]) => {
      acc[stage] = {
        count: stageDeals.length,
        value: stageDeals.reduce((sum, d) => sum + (Number(d.amount) || 0), 0),
      };
      return acc;
    }, {} as any);

    res.json({ pipeline, totals });
  } catch (error) {
    next(error);
  }
});

// Get deal by ID
router.get('/:id', auth, async (req, res, next) => {
  try {
    const { id } = req.params;
    
    const deal = await prisma.deal.findUnique({
      where: { id },
      include: {
        company: true,
        contact: true,
        owner: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
            email: true,
          },
        },
        activities: {
          orderBy: { createdAt: 'desc' },
          take: 20,
          include: {
            user: {
              select: {
                id: true,
                firstName: true,
                lastName: true,
              },
            },
          },
        },
      },
    });

    if (!deal) {
      return res.status(404).json({ error: 'Deal not found' });
    }

    res.json({ deal });
  } catch (error) {
    next(error);
  }
});

// Create deal
router.post('/', auth, validate(createDealSchema), async (req, res, next) => {
  try {
    const dealData: any = {
      ...req.body,
      ownerId: req.user!.id,
    };

    if (req.body.expectedClose) {
      dealData.expectedClose = new Date(req.body.expectedClose);
    }

    const deal = await prisma.deal.create({
      data: dealData,
      include: {
        company: {
          select: {
            id: true,
            name: true,
          },
        },
      },
    });

    // Create activity
    await prisma.activity.create({
      data: {
        type: 'status_change',
        subject: 'Deal créé',
        content: `Deal "${deal.title}" créé avec le statut ${deal.stage}`,
        dealId: deal.id,
        userId: req.user!.id,
      },
    });

    // Emit WebSocket event
    io.emit('deal:created', {
      deal,
      user: req.user,
    });

    logger.info(`Deal created: ${deal.title} by user ${req.user!.id}`);

    res.status(201).json({ deal });
  } catch (error) {
    next(error);
  }
});

// Update deal
router.put('/:id', auth, validate(createDealSchema), async (req, res, next) => {
  try {
    const { id } = req.params;
    
    // Get current deal for comparison
    const currentDeal = await prisma.deal.findUnique({
      where: { id },
    });

    if (!currentDeal) {
      return res.status(404).json({ error: 'Deal not found' });
    }

    const updateData: any = { ...req.body };
    if (req.body.expectedClose) {
      updateData.expectedClose = new Date(req.body.expectedClose);
    }

    const deal = await prisma.deal.update({
      where: { id },
      data: updateData,
      include: {
        company: {
          select: {
            id: true,
            name: true,
          },
        },
      },
    });

    // Track stage change
    if (currentDeal.stage !== deal.stage) {
      await prisma.activity.create({
        data: {
          type: 'status_change',
          subject: 'Changement de statut',
          content: `Statut changé de ${currentDeal.stage} à ${deal.stage}`,
          dealId: deal.id,
          userId: req.user!.id,
          metadata: {
            oldStage: currentDeal.stage,
            newStage: deal.stage,
          },
        },
      });

      // Handle won/lost
      if (deal.stage === 'WON') {
        await prisma.deal.update({
          where: { id },
          data: { wonAt: new Date() },
        });
      } else if (deal.stage === 'LOST') {
        await prisma.deal.update({
          where: { id },
          data: { lostAt: new Date() },
        });
      }
    }

    // Emit WebSocket event
    io.emit('deal:updated', {
      deal,
      user: req.user,
    });

    res.json({ deal });
  } catch (error) {
    next(error);
  }
});

// Update deal stage (quick action)
router.patch('/:id/stage', auth, async (req, res, next) => {
  try {
    const { id } = req.params;
    const { stage } = req.body;

    if (!stage || !['NEW', 'QUALIFIED', 'PROPOSAL', 'NEGOTIATION', 'WON', 'LOST'].includes(stage)) {
      return res.status(400).json({ error: 'Invalid stage' });
    }

    const currentDeal = await prisma.deal.findUnique({
      where: { id },
    });

    if (!currentDeal) {
      return res.status(404).json({ error: 'Deal not found' });
    }

    const updateData: any = { stage };
    
    // Set won/lost timestamps
    if (stage === 'WON') {
      updateData.wonAt = new Date();
      updateData.probability = 100;
    } else if (stage === 'LOST') {
      updateData.lostAt = new Date();
      updateData.probability = 0;
    }

    const deal = await prisma.deal.update({
      where: { id },
      data: updateData,
    });

    // Create activity
    await prisma.activity.create({
      data: {
        type: 'status_change',
        subject: 'Changement de statut',
        content: `Statut changé de ${currentDeal.stage} à ${stage}`,
        dealId: deal.id,
        userId: req.user!.id,
        metadata: {
          oldStage: currentDeal.stage,
          newStage: stage,
        },
      },
    });

    // Emit WebSocket event
    io.emit('deal:stage-changed', {
      dealId: id,
      oldStage: currentDeal.stage,
      newStage: stage,
      user: req.user,
    });

    res.json({ deal });
  } catch (error) {
    next(error);
  }
});

// Delete deal
router.delete('/:id', auth, async (req, res, next) => {
  try {
    const { id } = req.params;
    
    await prisma.deal.delete({
      where: { id },
    });

    res.json({ message: 'Deal deleted successfully' });
  } catch (error) {
    next(error);
  }
});

export { router as dealsRouter };