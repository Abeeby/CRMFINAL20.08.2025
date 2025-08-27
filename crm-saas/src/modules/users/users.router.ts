import { Router } from 'express';
import { z } from 'zod';
import { UserRole } from '@prisma/client';
import bcrypt from 'bcryptjs';
import { prisma } from '../../server';
import { auth, requireRole } from '../../middlewares/auth.middleware';
import { validate, validateParams, validateQuery } from '../../middlewares/validate.middleware';

const router = Router();

// Get all users (admin only)
router.get('/', auth, requireRole('ADMIN', 'HR'), async (req, res, next) => {
  try {
    const users = await prisma.user.findMany({
      select: {
        id: true,
        email: true,
        firstName: true,
        lastName: true,
        role: true,
        active: true,
        createdAt: true,
        lastLoginAt: true,
      },
      orderBy: { createdAt: 'desc' },
    });

    res.json({ users });
  } catch (error) {
    next(error);
  }
});

// Get user by ID
router.get('/:id', auth, async (req, res, next) => {
  try {
    const { id } = req.params;
    
    // Users can only view their own profile unless admin
    if (req.user!.id !== id && req.user!.role !== 'ADMIN') {
      return res.status(403).json({ error: 'Access denied' });
    }

    const user = await prisma.user.findUnique({
      where: { id },
      select: {
        id: true,
        email: true,
        firstName: true,
        lastName: true,
        role: true,
        locale: true,
        timezone: true,
        avatar: true,
        active: true,
        emailVerified: true,
        createdAt: true,
        lastLoginAt: true,
      },
    });

    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.json({ user });
  } catch (error) {
    next(error);
  }
});

// Update user
const updateUserSchema = z.object({
  firstName: z.string().optional(),
  lastName: z.string().optional(),
  locale: z.string().optional(),
  timezone: z.string().optional(),
  avatar: z.string().url().optional(),
});

router.put('/:id', auth, validate(updateUserSchema), async (req, res, next) => {
  try {
    const { id } = req.params;
    
    // Users can only update their own profile unless admin
    if (req.user!.id !== id && req.user!.role !== 'ADMIN') {
      return res.status(403).json({ error: 'Access denied' });
    }

    const user = await prisma.user.update({
      where: { id },
      data: req.body,
      select: {
        id: true,
        email: true,
        firstName: true,
        lastName: true,
        role: true,
        locale: true,
        timezone: true,
        avatar: true,
      },
    });

    res.json({ user });
  } catch (error) {
    next(error);
  }
});

// Change password
const changePasswordSchema = z.object({
  currentPassword: z.string(),
  newPassword: z.string().min(6),
});

router.post('/:id/change-password', auth, validate(changePasswordSchema), async (req, res, next) => {
  try {
    const { id } = req.params;
    const { currentPassword, newPassword } = req.body;
    
    // Users can only change their own password
    if (req.user!.id !== id) {
      return res.status(403).json({ error: 'Access denied' });
    }

    const user = await prisma.user.findUnique({
      where: { id },
    });

    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    // Verify current password
    const validPassword = await bcrypt.compare(currentPassword, user.passwordHash);
    if (!validPassword) {
      return res.status(400).json({ error: 'Current password is incorrect' });
    }

    // Hash new password
    const passwordHash = await bcrypt.hash(newPassword, 10);

    await prisma.user.update({
      where: { id },
      data: { passwordHash },
    });

    res.json({ message: 'Password changed successfully' });
  } catch (error) {
    next(error);
  }
});

export { router as usersRouter };