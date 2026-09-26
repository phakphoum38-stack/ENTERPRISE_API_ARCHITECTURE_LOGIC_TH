<?php

namespace App\Providers;

use Illuminate\Support\ServiceProvider;
use ResearchOS\Platform\Contracts\AuthorizationGateway;
use ResearchOS\Platform\Infrastructure\NullAuthorizationGateway;

final class AppServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        $this->app->bind(AuthorizationGateway::class, NullAuthorizationGateway::class);
    }

    public function boot(): void
    {
        //
    }
}
