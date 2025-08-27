import { Router } from 'express';
import { z } from 'zod';
import { prisma } from '../../server';
import { auth } from '../../middlewares/auth.middleware';
import { validate, validateQuery } from '../../middlewares/validate.middleware';

const router = Router();

const createCompanySchema = z.object({
  name: z.string().min(1),
  vat: z.string().optional(),
  website: z.string().url().optional(),
  industry: z.string().optional(),
  size: z.string().optional(),
  revenue: z.number().optional(),
  address: z.object({
    street: z.string().optional(),
    city: z.string().optional(),
    postalCode: z.string().optional(),
    country: z.string().optional(),
  }).optional(),
  tags: z.array(z.string()).optional(),
  notes: z.string().optional(),
});

// Get all companies
router.get('/', auth, async (req, res, next) => {
  try {
    const { search, tags, active = 'true' } = req.query;
    
    const where: any = {
      active: active === 'true',
    };

    if (search) {
      where.OR = [
        { name: { contains: search as string, mode: 'insensitive' } },
        { vat: { contains: search as string, mode: 'insensitive' } },
      ];
    }

    if (tags) {
      where.tags = {
        hasSome: (tags as string).split(','),
      };
    }

    const companies = await prisma.company.findMany({
      where,
      include: {
        owner: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
          },
        },
        _count: {
          select: {
            contacts: true,
            deals: true,
          },
        },
      },
      orderBy: { createdAt: 'desc' },
    });

    res.json({ companies });
  } catch (error) {
    next(error);
  }
});

// Get company by ID
router.get('/:id', auth, async (req, res, next) => {
  try {
    const { id } = req.params;
    
    const company = await prisma.company.findUnique({
      where: { id },
      include: {
        owner: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
            email: true,
          },
        },
        contacts: true,
        deals: {
          orderBy: { createdAt: 'desc' },
          take: 10,
        },
        tickets: {
          orderBy: { createdAt: 'desc' },
          take: 10,
        },
      },
    });

    if (!company) {
      return res.status(404).json({ error: 'Company not found' });
    }

    res.json({ company });
  } catch (error) {
    next(error);
  }
});

// Create company
router.post('/', auth, validate(createCompanySchema), async (req, res, next) => {
  try {
    const company = await prisma.company.create({
      data: {
        ...req.body,
        ownerId: req.user!.id,
      },
    });

    res.status(201).json({ company });
  } catch (error) {
    next(error);
  }
});

// Update company
router.put('/:id', auth, validate(createCompanySchema), async (req, res, next) => {
  try {
    const { id } = req.params;
    
    const company = await prisma.company.update({
      where: { id },
      data: req.body,
    });

    res.json({ company });
  } catch (error) {
    next(error);
  }
});

// Delete company (soft delete)
router.delete('/:id', auth, async (req, res, next) => {
  try {
    const { id } = req.params;
    
    await prisma.company.update({
      where: { id },
      data: { active: false },
    });

    res.json({ message: 'Company deleted successfully' });
  } catch (error) {
    next(error);
  }
});

export { router as companiesRouter };