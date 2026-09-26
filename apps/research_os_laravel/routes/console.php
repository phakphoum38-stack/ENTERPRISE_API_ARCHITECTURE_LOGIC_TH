<?php

use Illuminate\Support\Facades\Artisan;

Artisan::command('research-os:contract', function (): void {
    $this->info('Research OS Laravel Platform contract v1.0.0');
})->purpose('Report the Laravel Platform contract version.');
