import { Router } from 'express';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { z } from 'zod';
import { prisma } from '../../server';
import { validate } from '../../middlewares/validate.middleware';
import { auth } from '../../middlewares/auth.middleware';
import { logger } from '../../utils/logger';

const router = Router();

// Validation schemas
const registerSchema = z.object({
  email: z.string().email('Email invalide'),
  password: z.string().min(6, 'Le mot de passe doit contenir au moins 6 caractères'),
  firstName: z.string().optional(),
  lastName: z.string().optional(),
});

const loginSchema = z.object({
  email: z.string().email('Email invalide'),
  password: z.string().min(1, 'Mot de passe requis'),
});

// Register
router.post('/register', validate(registerSchema), async (req, res, next) => {
  try {
    const { email, password, firstName, lastName } = req.body;
    
    // Check if user already exists
    const existingUser = await prisma.user.findUnique({
      where: { email },
    });

    if (existingUser) {
      return res.status(400).json({ 
        error: 'Cet email est déjà utilisé' 
      });
    }
    
    // Hash password
    const passwordHash = await bcrypt.hash(password, 10);
    
    // Create user
    const user = await prisma.user.create({
      data: {
        email,
        passwordHash,
        firstName,
        lastName,
        role: 'EMPLOYEE', // Default role
      },
      select: {
        id: true,
        email: true,
        firstName: true,
        lastName: true,
        role: true,
        locale: true,
        timezone: true,
      },
    });
    
    // Generate tokens
    const accessToken = jwt.sign(
      { id: user.id, email: user.email, role: user.role },
      process.env.JWT_SECRET!,
      { expiresIn: process.env.JWT_EXPIRES_IN || '15m' }
    );
    
    const refreshToken = jwt.sign(
      { id: user.id },
      process.env.JWT_REFRESH_SECRET!,
      { expiresIn: process.env.JWT_REFRESH_EXPIRES_IN || '7d' }
    );

    // Save refresh token
    await prisma.user.update({
      where: { id: user.id },
      data: { refreshToken },
    });
    
    // Set cookies
    res.cookie('accessToken', accessToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 15 * 60 * 1000, // 15 minutes
    });
    
    res.cookie('refreshToken', refreshToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
    });

    logger.info(`New user registered: ${email}`);
    
    res.status(201).json({ 
      message: 'Inscription réussie',
      user,
      accessToken, // Also return in body for non-cookie clients
    });
  } catch (error) {
    next(error);
  }
});

// Login
router.post('/login', validate(loginSchema), async (req, res, next) => {
  try {
    const { email, password } = req.body;
    
    // Find user with password
    const user = await prisma.user.findUnique({
      where: { email },
    });
    
    if (!user) {
      return res.status(401).json({ 
        error: 'Email ou mot de passe incorrect' 
      });
    }

    // Verify password
    const validPassword = await bcrypt.compare(password, user.passwordHash);
    
    if (!validPassword) {
      return res.status(401).json({ 
        error: 'Email ou mot de passe incorrect' 
      });
    }

    // Check if account is active
    if (!user.active) {
      return res.status(403).json({ 
        error: 'Compte désactivé' 
      });
    }
    
    // Generate tokens
    const accessToken = jwt.sign(
      { id: user.id, email: user.email, role: user.role },
      process.env.JWT_SECRET!,
      { expiresIn: process.env.JWT_EXPIRES_IN || '15m' }
    );
    
    const refreshToken = jwt.sign(
      { id: user.id },
      process.env.JWT_REFRESH_SECRET!,
      { expiresIn: process.env.JWT_REFRESH_EXPIRES_IN || '7d' }
    );
    
    // Update last login and refresh token
    await prisma.user.update({
      where: { id: user.id },
      data: { 
        lastLoginAt: new Date(),
        refreshToken,
      },
    });
    
    // Set cookies
    res.cookie('accessToken', accessToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 15 * 60 * 1000, // 15 minutes
    });
    
    res.cookie('refreshToken', refreshToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
    });

    // Return user without password
    const { passwordHash, refreshToken: _, ...userWithoutSensitive } = user;

    logger.info(`User logged in: ${email}`);
    
    res.json({ 
      message: 'Connexion réussie',
      user: userWithoutSensitive,
      accessToken, // Also return in body for non-cookie clients
    });
  } catch (error) {
    next(error);
  }
});

// Logout
router.post('/logout', auth, async (req, res, next) => {
  try {
    // Clear refresh token in database
    await prisma.user.update({
      where: { id: req.user!.id },
      data: { refreshToken: null },
    });
    
    // Clear cookies
    res.clearCookie('accessToken');
    res.clearCookie('refreshToken');

    logger.info(`User logged out: ${req.user!.email}`);
    
    res.json({ 
      message: 'Déconnexion réussie' 
    });
  } catch (error) {
    next(error);
  }
});

// Get current user
router.get('/me', auth, async (req, res, next) => {
  try {
    const user = await prisma.user.findUnique({
      where: { id: req.user!.id },
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
      return res.status(404).json({ 
        error: 'Utilisateur non trouvé' 
      });
    }
    
    res.json({ user });
  } catch (error) {
    next(error);
  }
});

// Refresh token
router.post('/refresh', async (req, res, next) => {
  try {
    const refreshToken = req.cookies?.refreshToken || req.body.refreshToken;
    
    if (!refreshToken) {
      return res.status(401).json({ 
        error: 'Refresh token manquant' 
      });
    }
    
    // Verify refresh token
    let decoded;
    try {
      decoded = jwt.verify(refreshToken, process.env.JWT_REFRESH_SECRET!) as { id: string };
    } catch (err) {
      return res.status(401).json({ 
        error: 'Refresh token invalide' 
      });
    }
    
    // Find user and verify refresh token matches
    const user = await prisma.user.findUnique({
      where: { id: decoded.id },
      select: {
        id: true,
        email: true,
        role: true,
        refreshToken: true,
        active: true,
      },
    });
    
    if (!user || user.refreshToken !== refreshToken) {
      return res.status(401).json({ 
        error: 'Refresh token invalide' 
      });
    }

    if (!user.active) {
      return res.status(403).json({ 
        error: 'Compte désactivé' 
      });
    }
    
    // Generate new access token
    const newAccessToken = jwt.sign(
      { id: user.id, email: user.email, role: user.role },
      process.env.JWT_SECRET!,
      { expiresIn: process.env.JWT_EXPIRES_IN || '15m' }
    );
    
    // Set new access token cookie
    res.cookie('accessToken', newAccessToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 15 * 60 * 1000, // 15 minutes
    });

    logger.info(`Token refreshed for user: ${user.email}`);
    
    res.json({ 
      message: 'Token actualisé',
      accessToken: newAccessToken,
    });
  } catch (error) {
    next(error);
  }
});

export { router as authRouter };