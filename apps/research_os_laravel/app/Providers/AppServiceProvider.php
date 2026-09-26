<?php

namespace App\Providers;

use Illuminate\Support\ServiceProvider;
use ResearchOS\Platform\Contracts\AuditGateway;
use ResearchOS\Platform\Contracts\AuthorizationGateway;
use ResearchOS\Platform\Contracts\EvidenceGateway;
use ResearchOS\Platform\Contracts\IdentityGateway;
use ResearchOS\Platform\Contracts\MessagingGateway;
use ResearchOS\Platform\Contracts\WorkflowGateway;
use ResearchOS\Platform\Infrastructure\CanonicalAuditGateway;
use ResearchOS\Platform\Infrastructure\CanonicalAuthorizationGateway;
use ResearchOS\Platform\Infrastructure\CanonicalEvidenceGateway;
use ResearchOS\Platform\Infrastructure\CanonicalIdentityGateway;
use ResearchOS\Platform\Infrastructure\CanonicalMessagingGateway;
use ResearchOS\Platform\Infrastructure\CanonicalPlatformClient;
use ResearchOS\Platform\Infrastructure\CanonicalWorkflowGateway;

final class AppServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        $this->app->singleton(CanonicalPlatformClient::class, fn () => new CanonicalPlatformClient(
            new \Illuminate\Http\Client\Factory(),
            (string) config('platform.canonical.base_url', ''),
            (float) config('platform.canonical.timeout', 10),
            (float) config('platform.canonical.connect_timeout', 3),
        ));

        $this->app->bind(IdentityGateway::class, CanonicalIdentityGateway::class);
        $this->app->bind(AuthorizationGateway::class, CanonicalAuthorizationGateway::class);
        $this->app->bind(WorkflowGateway::class, CanonicalWorkflowGateway::class);
        $this->app->bind(MessagingGateway::class, CanonicalMessagingGateway::class);
        $this->app->bind(EvidenceGateway::class, CanonicalEvidenceGateway::class);
        $this->app->bind(AuditGateway::class, CanonicalAuditGateway::class);
    }

    public function boot(): void
    {
        //
    }
}
