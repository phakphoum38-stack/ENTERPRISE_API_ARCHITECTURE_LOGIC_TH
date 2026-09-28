<?php

declare(strict_types=1);

namespace Tests\Unit;

use Illuminate\Http\Client\Request;
use Illuminate\Http\Client\Factory;
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
    private Factory $http;

    protected function setUp(): void
    {
        parent::setUp();
        $this->http = new Factory();
        $this->context = new RequestContext('req-123', 'corr-456', 'owner', '1.0.0');
        $this->client = new CanonicalPlatformClient($this->http, 'https://platform.example.test');
    }

    public function testAuthorizationReturnsCanonicalDecision(): void
    {
        $captured = [];
        $this->client = new CanonicalPlatformClient(
            $this->http,
            'https://platform.example.test',
            transport: function (RequestContext $context, string $endpoint, array $payload) use (&$captured): array {
                $captured = [$context, $endpoint, $payload];
                return ['decision' => 'ALLOWED'];
            },
        );

        $decision = (new CanonicalAuthorizationGateway($this->client, '/api/v1/platform/authorization/decide'))
            ->decide($this->context, 'workflow.execute', 'workflow:demo');

        self::assertSame(AuthorizationDecision::ALLOWED, $decision);
        self::assertSame($this->context, $captured[0]);
        self::assertSame('/api/v1/platform/authorization/decide', $captured[1]);
        self::assertSame(['capability' => 'workflow.execute', 'resource' => 'workflow:demo'], $captured[2]);
    }

    public function testAuthorizationFailsClosedForTransportOrMalformedDecision(): void
    {
        $this->client = new CanonicalPlatformClient(
            $this->http,
            'https://platform.example.test',
            transport: fn (RequestContext $context, string $endpoint, array $payload): array => ['decision' => 'NOT_A_DECISION'],
        );
        self::assertSame(
            AuthorizationDecision::UNKNOWN,
            (new CanonicalAuthorizationGateway($this->client, '/api/v1/platform/authorization/decide'))
                ->decide($this->context, 'workflow.execute', 'workflow:demo')
        );

        $this->client = new CanonicalPlatformClient(
            $this->http,
            'https://platform.example.test',
            transport: function (RequestContext $context, string $endpoint, array $payload): array {
                throw new \RuntimeException('transport down');
            },
        );
        self::assertSame(
            AuthorizationDecision::UNKNOWN,
            (new CanonicalAuthorizationGateway($this->client, '/api/v1/platform/authorization/decide'))
                ->decide($this->context, 'workflow.execute', 'workflow:demo')
        );
    }

    public function testWorkflowMessagingEvidenceAndAuditRequireCanonicalIdentifiers(): void
    {
        $this->client = new CanonicalPlatformClient(
            $this->http,
            'https://platform.example.test',
            transport: function (RequestContext $context, string $endpoint, array $payload): array {
                return match ($endpoint) {
                    '/api/v1/platform/workflow/dispatch' => ['run_id' => 'run-1'],
                    '/api/v1/platform/messaging/publish' => ['message_id' => 'msg-1'],
                    '/api/v1/platform/evidence' => ['evidence_id' => 'evidence-1'],
                    '/api/v1/platform/audit' => ['audit_id' => 'audit-1'],
                    default => [],
                };
            },
        );

        self::assertSame(
            ['run_id' => 'run-1'],
            (new CanonicalWorkflowGateway($this->client, '/api/v1/platform/workflow/dispatch'))->dispatch($this->context, 'workflow.start', ['id' => 'w1'])
        );
        self::assertSame(
            'msg-1',
            (new CanonicalMessagingGateway($this->client, '/api/v1/platform/messaging/publish'))->publish($this->context, 'workflow.events', ['id' => 'w1'])
        );
        self::assertSame(
            'evidence-1',
            (new CanonicalEvidenceGateway($this->client, '/api/v1/platform/evidence'))->record($this->context, ['type' => 'workflow.started'])
        );
        self::assertSame(
            'audit-1',
            (new CanonicalAuditGateway($this->client, '/api/v1/platform/audit'))->record($this->context, ['action' => 'workflow.start'])
        );
    }

    public function testIdentityRequiresCanonicalIdentity(): void
    {
        $this->client = new CanonicalPlatformClient(
            $this->http,
            'https://platform.example.test',
            transport: fn (RequestContext $context, string $endpoint, array $payload): array => ['identity' => 'identity-1'],
        );

        self::assertSame(
            'identity-1',
            (new CanonicalIdentityGateway($this->client, '/api/v1/platform/identity/resolve'))->resolve($this->context)
        );
    }
}
