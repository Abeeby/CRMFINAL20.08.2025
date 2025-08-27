import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Démarrage du seeding...');

  // Créer l'utilisateur admin
  const adminPassword = await bcrypt.hash('Admin123!', 10);
  const admin = await prisma.user.upsert({
    where: { email: 'admin@test.com' },
    update: {},
    create: {
      email: 'admin@test.com',
      passwordHash: adminPassword,
      firstName: 'Admin',
      lastName: 'System',
      role: 'ADMIN',
      emailVerified: true,
    },
  });

  console.log('✅ Admin créé:', admin.email);

  // Créer un utilisateur employé
  const userPassword = await bcrypt.hash('User123!', 10);
  const user = await prisma.user.upsert({
    where: { email: 'user@test.com' },
    update: {},
    create: {
      email: 'user@test.com',
      passwordHash: userPassword,
      firstName: 'Jean',
      lastName: 'Dupont',
      role: 'EMPLOYEE',
      emailVerified: true,
    },
  });

  console.log('✅ Utilisateur créé:', user.email);

  // Créer un sales manager
  const salesPassword = await bcrypt.hash('Sales123!', 10);
  const salesManager = await prisma.user.upsert({
    where: { email: 'sales@test.com' },
    update: {},
    create: {
      email: 'sales@test.com',
      passwordHash: salesPassword,
      firstName: 'Marie',
      lastName: 'Commercial',
      role: 'SALES_MANAGER',
      emailVerified: true,
    },
  });

  console.log('✅ Sales Manager créé:', salesManager.email);

  // Créer des entreprises
  const company1 = await prisma.company.create({
    data: {
      name: 'TechCorp SA',
      vat: 'FR123456789',
      website: 'https://techcorp.example.com',
      industry: 'Technology',
      size: '50-200',
      revenue: 5000000,
      street: '123 Avenue des Champs',
      city: 'Paris',
      postalCode: '75008',
      country: 'France',
      ownerId: salesManager.id,
      tags: 'client,premium,tech',
    },
  });

  const company2 = await prisma.company.create({
    data: {
      name: 'Innovation Solutions',
      vat: 'FR987654321',
      website: 'https://innosolutions.example.com',
      industry: 'Consulting',
      size: '10-50',
      revenue: 1500000,
      street: '45 Rue de la République',
      city: 'Lyon',
      postalCode: '69001',
      country: 'France',
      ownerId: salesManager.id,
      tags: 'prospect,consulting',
    },
  });

  console.log('✅ Entreprises créées');

  // Créer des contacts
  const contact1 = await prisma.contact.create({
    data: {
      firstName: 'Marie',
      lastName: 'Directrice',
      email: 'marie.directrice@techcorp.com',
      phone: '+33 1 23 45 67 89',
      jobTitle: 'CEO',
      department: 'Direction',
      companyId: company1.id,
      tags: 'decision-maker,vip',
      consentEmail: true,
      consentPhone: true,
      consentMarketing: false,
    },
  });

  const contact2 = await prisma.contact.create({
    data: {
      firstName: 'Pierre',
      lastName: 'Martin',
      email: 'pierre.martin@innosolutions.com',
      phone: '+33 1 98 76 54 32',
      jobTitle: 'CTO',
      department: 'IT',
      companyId: company2.id,
      tags: 'technical,influencer',
      consentEmail: true,
      consentPhone: false,
      consentMarketing: true,
    },
  });

  console.log('✅ Contacts créés');

  // Créer des deals
  await prisma.deal.createMany({
    data: [
      {
        title: 'Nouveau projet TechCorp - Migration Cloud',
        stage: 'QUALIFIED',
        amount: 50000,
        currency: 'EUR',
        probability: 70,
        expectedClose: new Date('2024-03-31'),
        source: 'Website',
        companyId: company1.id,
        contactId: contact1.id,
        ownerId: salesManager.id,
        tags: 'cloud,migration,q1-2024',
      },
      {
        title: 'Contrat de consulting annuel',
        stage: 'PROPOSAL',
        amount: 120000,
        currency: 'EUR',
        probability: 50,
        expectedClose: new Date('2024-04-15'),
        source: 'Referral',
        companyId: company2.id,
        contactId: contact2.id,
        ownerId: salesManager.id,
        tags: 'consulting,annuel',
      },
      {
        title: 'Formation équipe TechCorp',
        stage: 'NEW',
        amount: 15000,
        currency: 'EUR',
        probability: 30,
        expectedClose: new Date('2024-05-01'),
        source: 'Upsell',
        companyId: company1.id,
        ownerId: salesManager.id,
        tags: 'formation,upsell',
      },
    ],
  });

  console.log('✅ Deals créés');

  // Créer des tickets
  const ticket1 = await prisma.ticket.create({
    data: {
      number: 'TK-2024-0001',
      subject: 'Problème de connexion au CRM',
      description: 'Je ne parviens pas à me connecter au CRM depuis ce matin. J\'ai essayé de réinitialiser mon mot de passe mais sans succès.',
      status: 'OPEN',
      priority: 'HIGH',
      companyId: company1.id,
      contactId: contact1.id,
      assigneeId: admin.id,
      tags: 'login,urgent',
    },
  });

  await prisma.ticketMessage.create({
    data: {
      ticketId: ticket1.id,
      authorEmail: 'support@crm-saas.com',
      authorName: 'Support Team',
      content: 'Bonjour, nous avons bien reçu votre demande. Pouvez-vous nous indiquer le message d\'erreur exact que vous recevez ?',
      internal: false,
    },
  });

  const ticket2 = await prisma.ticket.create({
    data: {
      number: 'TK-2024-0002',
      subject: 'Demande de nouvelle fonctionnalité',
      description: 'Serait-il possible d\'ajouter un export Excel pour les rapports ?',
      status: 'NEW',
      priority: 'LOW',
      companyId: company2.id,
      contactId: contact2.id,
      tags: 'feature-request,export',
    },
  });

  console.log('✅ Tickets créés');

  // Créer quelques pointages pour l'utilisateur employé
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  // Pointage du matin
  await prisma.attendance.create({
    data: {
      employeeId: user.id,
      type: 'IN_MORNING',
      timestamp: new Date(today.getTime() + 8 * 60 * 60 * 1000), // 8h00
      source: 'WEB',
      anomaly: 'NONE',
      locationLat: 48.8566,
      locationLng: 2.3522,
      locationAddress: 'Paris, France',
    },
  });

  await prisma.attendance.create({
    data: {
      employeeId: user.id,
      type: 'OUT_MORNING',
      timestamp: new Date(today.getTime() + 12 * 60 * 60 * 1000), // 12h00
      source: 'WEB',
      anomaly: 'NONE',
    },
  });

  console.log('✅ Pointages créés');

  // Créer des activités
  await prisma.activity.createMany({
    data: [
      {
        type: 'note',
        subject: 'Premier contact avec TechCorp',
        content: 'Discussion très positive, le client est intéressé par notre solution cloud.',
        dealId: null,
        userId: salesManager.id,
      },
      {
        type: 'email',
        subject: 'Proposition commerciale envoyée',
        content: 'Envoi de la proposition détaillée pour le projet de migration.',
        userId: salesManager.id,
      },
      {
        type: 'call',
        subject: 'Appel de suivi',
        content: 'Appel de 30 minutes pour discuter des détails techniques.',
        userId: salesManager.id,

      },
    ],
  });

  console.log('✅ Activités créées');

  console.log('✨ Seeding terminé avec succès!');
  console.log('');
  console.log('📧 Comptes de test:');
  console.log('  Admin    : admin@test.com / Admin123!');
  console.log('  User     : user@test.com / User123!');
  console.log('  Sales    : sales@test.com / Sales123!');
}

main()
  .catch((e) => {
    console.error('❌ Erreur lors du seeding:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });