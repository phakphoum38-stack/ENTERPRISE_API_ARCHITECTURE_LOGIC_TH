<?php

declare(strict_types=1);

namespace Tests\Unit;

use Illuminate\Http\Client\Request;
use Illuminate\Support\Facades\Http;
use ResearchOS\Platform\Contracts\AuthorizationDecision;
use ResearchOS\Platform\Contracts\RequestContext;
use ResearchOS\Platform\Infrastructure\CanonicalAuditGateway;
use ResearchOS\Platform\Infrastructure\CanonicalAuthorizationGateway;
use ResearchOS\Platform\Infrastructure\CanonicalEvidenceGateway;
use ResearchOS\Platform\Infrastructure\CanonicalIdentityGateway;
use ResearchOS\Platform\Infrastructure\CanonicalMessagingGateway;
use ResearchOS\Platform\Infrastructure\CanonicalPlatformClient;
use ResearchOS\Platform\Infrastructure\CanonicalWorkflowGateway;
use PHPUnit\Framework\TestCase;

final class CanonicalPlatformAdapterTest extends TestCase
{
    private RequestContext $context;
    private CanonicalPlatformClient $client;

    protected function setUp(): void
    {
        parent::setUp();
        config()->set('platform.canonical.base_url', 'https://platform.example.test');
        Http::fake();
        $this->context = new RequestContext('req-123', 'corr-456', 'owner', '1.0.0');
        $this->client = app(CanonicalPlatformClient::class);
    }

    public function testAuthorizationReturnsCanonicalDecision(): void
    {
        Http::fake(['*' => Http::response(['decision' => 'ALLOWED'], 200)]);

        $decision = (new CanonicalAuthorizationGateway($this->client))
            ->decide($this->context, 'workflow.execute', 'workflow:demo');

        self::assertSame(AuthorizationDecision::ALLOWED, $decision);
        Http::assertSent(fn (Request $request) =>
            $request->url() === 'https://platform.example.test/api/v1/platform/authorization/decide'
            && $request->header('X-Request-Id')[0] === 'req-123'
            && $request->header('X-Correlation-Id')[0] === 'corr-456'
            && $request->header('Idempotency-Key')[0] === 'req-123'
        );
    }

    public function testAuthorizationFailsClosedForTransportOrMalformedDecision(): void
    {
        Http::fake(['*' => Http::response(['decision' => 'NOT_A_DECISION'], 200)]);

        self::assertSame(
            AuthorizationDecision::UNKNOWN,
            (new CanonicalAuthorizationGateway($this->client))
                ->decide($this->context, 'workflow.execute', 'workflow:demo')
        );

        Http::fake(['*' => Http::response([], 503)]);
        self::assertSame(
            AuthorizationDecision::UNKNOWN,
            (new CanonicalAuthorizationGateway($this->client))
                ->decide($this->context, 'workflow.execute', 'workflow:demo')
        );
    }

    public function testWorkflowMessagingEvidenceAndAuditRequireCanonicalIdentifiers(): void
    {
        Http::fakeSequence()
            ->push(['run_id' => 'run-1'], 200)
            ->push(['message_id' => 'msg-1'], 200)
            ->push(['evidence_id' => 'evidence-1'], 200)
            ->push(['audit_id' => 'audit-1'], 200);

        self::assertSame(
            ['run_id' => 'run-1'],
            (new CanonicalWorkflowGateway($this->client))->dispatch($this->context, 'workflow.start', ['id' => 'w1'])
        );
        self::assertSame(
            'msg-1',
            (new CanonicalMessagingGateway($this->client))->publish($this->context, 'workflow.events', ['id' => 'w1'])
        );
        self::assertSame(
            'evidence-1',
            (new CanonicalEvidenceGateway($this->client))->record($this->context, ['type' => 'workflow.started'])
        );
        self::assertSame(
            'audit-1',
            (new CanonicalAuditGateway($this->client))->record($this->context, ['action' => 'workflow.start'])
        );
    }

    public function testIdentityRequiresCanonicalIdentity(): void
    {
        Http::fake(['*' => Http::response(['identity' => 'identity-1'], 200)]);

        self::assertSame(
            'identity-1',
            (new CanonicalIdentityGateway($this->client))->resolve($this->context)
        );
    }
}
