import { headers } from 'next/headers';
import { NextResponse } from 'next/server';
import { Webhook } from 'svix';

type WebhookEvent = {
  type: string;
  data: Record<string, unknown>;
};

export async function POST(req: Request) {
  const WEBHOOK_SECRET = process.env.CLERK_WEBHOOK_SECRET;

  if (!WEBHOOK_SECRET) {
    return NextResponse.json(
      { error: 'Webhook secret not configured' },
      { status: 500 }
    );
  }

  const headerPayload = await headers();
  const svixId = headerPayload.get('svix-id');
  const svixTimestamp = headerPayload.get('svix-timestamp');
  const svixSignature = headerPayload.get('svix-signature');

  if (!svixId || !svixTimestamp || !svixSignature) {
    return NextResponse.json(
      { error: 'Missing svix headers' },
      { status: 400 }
    );
  }

  const payload = await req.json();
  const body = JSON.stringify(payload);

  const wh = new Webhook(WEBHOOK_SECRET);
  let event: WebhookEvent;

  try {
    event = wh.verify(body, {
      'svix-id': svixId,
      'svix-timestamp': svixTimestamp,
      'svix-signature': svixSignature,
    }) as WebhookEvent;
  } catch {
    return NextResponse.json(
      { error: 'Invalid webhook signature' },
      { status: 400 }
    );
  }

  switch (event.type) {
    case 'user.created':
      // Handle new user creation - sync to your database
      console.log('New user created:', event.data.id);
      break;
    case 'user.updated':
      // Handle user profile updates
      console.log('User updated:', event.data.id);
      break;
    case 'user.deleted':
      // Handle user deletion
      console.log('User deleted:', event.data.id);
      break;
    default:
      console.log('Unhandled webhook event:', event.type);
  }

  return NextResponse.json({ received: true });
}
