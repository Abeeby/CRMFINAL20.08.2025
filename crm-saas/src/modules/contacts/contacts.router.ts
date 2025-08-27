import { Router } from 'express';
import { z } from 'zod';
import { prisma } from '../../server';
import { auth } from '../../middlewares/auth.middleware';
import { validate } from '../../middlewares/validate.middleware';

const router = Router();

const createContactSchema = z.object({
  firstName: z.string().min(1),
  lastName: z.string().min(1),
  email: z.string().email().optional(),
  phone: z.string().optional(),
  mobile: z.string().optional(),
  jobTitle: z.string().optional(),
  department: z.string().optional(),
  companyId: z.string().optional(),
  address: z.object({
    street: z.string().optional(),
    city: z.string().optional(),
    postalCode: z.string().optional(),
    country: z.string().optional(),
  }).optional(),
  tags: z.array(z.string()).optional(),
  notes: z.string().optional(),
  consents: z.object({
    email: z.boolean().optional(),
    phone: z.boolean().optional(),
    marketing: z.boolean().optional(),
  }).optional(),
});

// Get all contacts
router.get('/', auth, async (req, res, next) => {
  try {
    const { search, companyId, tags } = req.query;
    
    const where: any = {
      active: true,
    };

    if (search) {
      where.OR = [
        { firstName: { contains: search as string, mode: 'insensitive' } },
        { lastName: { contains: search as string, mode: 'insensitive' } },
        { email: { contains: search as string, mode: 'insensitive' } },
      ];
    }

    if (companyId) {
      where.companyId = companyId;
    }

    if (tags) {
      where.tags = {
        hasSome: (tags as string).split(','),
      };
    }

    const contacts = await prisma.contact.findMany({
      where,
      include: {
        company: {
          select: {
            id: true,
            name: true,
          },
        },
      },
      orderBy: { createdAt: 'desc' },
    });

    res.json({ contacts });
  } catch (error) {
    next(error);
  }
});

// Get contact by ID
router.get('/:id', auth, async (req, res, next) => {
  try {
    const { id } = req.params;
    
    const contact = await prisma.contact.findUnique({
      where: { id },
      include: {
        company: true,
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

    if (!contact) {
      return res.status(404).json({ error: 'Contact not found' });
    }

    res.json({ contact });
  } catch (error) {
    next(error);
  }
});

// Create contact
router.post('/', auth, validate(createContactSchema), async (req, res, next) => {
  try {
    const contact = await prisma.contact.create({
      data: req.body,
    });

    res.status(201).json({ contact });
  } catch (error) {
    next(error);
  }
});

// Update contact
router.put('/:id', auth, validate(createContactSchema), async (req, res, next) => {
  try {
    const { id } = req.params;
    
    const contact = await prisma.contact.update({
      where: { id },
      data: req.body,
    });

    res.json({ contact });
  } catch (error) {
    next(error);
  }
});

// Delete contact (soft delete)
router.delete('/:id', auth, async (req, res, next) => {
  try {
    const { id } = req.params;
    
    await prisma.contact.update({
      where: { id },
      data: { active: false },
    });

    res.json({ message: 'Contact deleted successfully' });
  } catch (error) {
    next(error);
  }
});

export { router as contactsRouter };